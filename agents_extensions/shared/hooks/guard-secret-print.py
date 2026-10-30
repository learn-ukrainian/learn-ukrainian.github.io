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

It also refuses process kills that would reach the agent's own shell, its
harness or an ancestor. Kill sites (`kill`, `pkill`, `killall`, and `pgrep` or
`pidof` feeding a non-literal `kill`) are resolved against the live process
table with procps' own selection; full-command-line selections are refused,
since the agent's shell holds the command. Shell text the guard cannot read
(a shell fed by a pipe, `eval` of an unknown value, `env -S`, a command name
it cannot resolve) is refused too. The secret override does not apply to any
of these, nor to a command too deep or malformed to read whole.

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
# Process kills (#12118): kill sites are paired per invocation without data
# flow, so a selector reaching a protected process beside any non-literal kill
# is refused. The process reader models shell grammar and the effects it found
# carried through indirection (IFS, echo bindings, written or renamed files),
# read to a fixpoint; an effect carried through a form it does not model is a
# limit. Code in other languages (`python -c` with os.kill, awk system()), files
# the command does not write, functions and aliases defined outside the command
# text, and kill operands from sources other than pgrep and pidof (`ps | awk`,
# `lsof -t`, PID files) are not read. Only an execution-time control sees all.

from __future__ import annotations

import codecs
import getopt
import json
import os
import pwd
import re
import shlex
import shutil
import signal
import subprocess
import sys

# Use the sibling helper in either the source tree or a deployed hook copy.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Don't write __pycache__ next to deployed hooks (#9108).
sys.dont_write_bytecode = True
try:
    from shell_redirects import _redirect_target_dynamic
    from shell_shlex import (
        ShellPreprocessLimit,
        normalize_io_descriptors,
        preprocess_shell_command,
        skippable_heredoc_delimiters,
        split_operator_run,
        split_quote_preserving,
        strip_skippable_heredoc_bodies,
    )
    from shell_shlex import (
        _quote_after as shell_quote_after,
    )
except Exception as exc:
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


def _separate_program_flag_quotes(command: str, *, keep_plain: bool = False) -> str:
    """Give shlex's non-POSIX lexer a word boundary before attached scripts.

    With `keep_plain`, a flag whose attached quote holds no blank, operator or
    escape stays one word, as the shell reads it (`-e'c'` is `-ec`).
    """
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
            if (
                flag
                and keep_plain
                and re.match(r"""'[^'\s();&|<>]*'|"[^"\\\s();&|<>]*\"""", command[index + flag.end() :])
            ):
                flag = None
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


def _join_shell_words(text: str, tokens: list[str]) -> list[str]:
    """Rejoin the quote fragments of one shell word (`'pk'"ill"`) that the lexer split.

    The lexer ends a token after its closing quote, so tokens that touch in
    `text` belong to one word unless either is an operator.
    """
    words: list[str] = []
    end = 0
    joinable = False
    for token in tokens:
        start = text.find(token, end)
        if start < 0:
            raise ValueError("token not found in its source text")
        word = not set(token) <= set("();&|<>\n")
        if joinable and word and start == end:
            words[-1] += token
        else:
            words.append(token)
        end = start + len(token)
        joinable = word
    return words


def _tokenize(command: str, *, shell_words: bool = False) -> list[str]:
    """Split a command into tokens; with `shell_words`, into the words the shell reads."""
    try:
        executable = _decode_ansi_c_quotes(preprocess_shell_command(command))
        protected, parameters = _protect_parameters(_separate_program_flag_quotes(executable, keep_plain=shell_words))

        def descriptor_word(descriptor: str, operator: str) -> str:
            marker = f"\ue000{len(parameters)}\ue001"
            while marker in protected:
                marker += "\ue002"
            parameters[marker] = descriptor + operator
            return marker + " "

        protected = normalize_io_descriptors(protected, descriptor_word)
        tokens = split_quote_preserving(protected, punctuation_chars="();&|<>\n", whitespace=" \t")
        if shell_words:
            tokens = _join_shell_words(protected, tokens)
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


# ANSI-C escapes that unicode_escape decodes as Bash does: named controls, quotes,
# and two-digit hex or octal for a nonzero ASCII byte. Bash truncates at NUL, wraps
# octal past \377, emits raw bytes past \x7f and reads \e, \c, \u and \? differently.
_ANSI_C_MODELLED_ESCAPE = re.compile(r"\\(?:[abfnrtv\\'\"]|x([0-9A-Fa-f]{2})|([0-7]{1,3}))")


def _ansi_c_modelled(body: str) -> bool:
    index = body.find("\\")
    while index >= 0:
        match = _ANSI_C_MODELLED_ESCAPE.match(body, index)
        if match is None:
            return False
        if match[1] or match[2]:
            value = int(match[1], 16) if match[1] else int(match[2], 8)
            if not 0 < value < 0x80:
                return False
        index = body.find("\\", match.end())
    return True


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
                body = command[i + 2 : end]
                if not _ansi_c_modelled(body):
                    raise ValueError("ANSI-C escape whose Bash meaning is not modelled")
                value = codecs.decode(body, "unicode_escape")
                quoted = shlex.quote(value)
                out.append(quoted if quoted.startswith("'") else "'" + quoted + "'")
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


def _pipelines(command: str, *, shell_words: bool = False) -> list[list[list[str]]]:
    """Return command pipelines, split quote-aware on pipes and separators."""
    # shlex groups adjacent punctuation into runs such as `);`. Split those
    # before segmenting, or a command after a substitution can be hidden.
    tokens = [part for token in _tokenize(command, shell_words=shell_words) for part in split_operator_run(token)]
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


# Wrapper: (short options taking a value, long options taking a value,
# short and long options that only look a command up and never run it,
# positional operands before the command).
_WRAPPER_OPTIONS = {
    "sudo": (
        "CDghpRrtTUu",
        {
            "--chdir",
            "--chroot",
            "--close-from",
            "--command-timeout",
            "--group",
            "--host",
            "--other-user",
            "--prompt",
            "--role",
            "--type",
            "--user",
        },
        {"-e", "-K", "-l", "-V", "-v", "--edit", "--list", "--remove-timestamp", "--validate", "--version"},
        0,
    ),
    "exec": ("a", set(), set(), 0),
    "time": ("fo", {"--format", "--output"}, set(), 0),
    "nice": ("n", {"--adjustment"}, set(), 0),
    "stdbuf": ("ioe", {"--input", "--output", "--error"}, set(), 0),
    "timeout": ("ks", {"--kill-after", "--signal"}, set(), 1),
    "command": ("", set(), {"-v", "-V"}, 0),
    "nohup": ("", set(), set(), 0),
    "builtin": ("", set(), set(), 0),
    "busybox": ("", set(), {"--help", "--install", "--list", "--list-full"}, 0),
}


def _after_wrapper_options(seg: list[str], i: int, wrapper: str, redirects: list[str]) -> int:
    """Return the index after a wrapper's options and operands, or -1 for a lookup.

    Redirections may sit anywhere among them; they are moved to `redirects`.
    """
    value_letters, value_longs, lookups, positionals = _WRAPPER_OPTIONS[wrapper]
    value_pending = False
    options = True
    while i < len(seg):
        skip = _redirection_skip_count(seg[i])
        if skip:
            redirects.extend(seg[i : i + skip])
            i += skip
            continue
        word = _strip_quotes(seg[i])
        if value_pending:
            value_pending = False
            i += 1
            continue
        if options and word == "--":
            options = False
            i += 1
            continue
        if not options or not word.startswith("-") or word == "-":
            if not positionals:
                return i
            positionals -= 1
            options = False
            i += 1
            continue
        i += 1
        if word.startswith("--"):
            name = word.split("=", 1)[0]
            if name in lookups:
                return -1
            value_pending = name in value_longs and "=" not in word
            continue
        for index, letter in enumerate(word[1:], 1):
            if f"-{letter}" in lookups:
                return -1
            if letter in value_letters:
                value_pending = index == len(word) - 1
                break
    return i


def _command_at(seg: list[str]) -> tuple[str, list[str], int] | None:
    """Return `(command, raw_args, index)` after simple wrappers/assignments."""
    i = 0
    redirects: list[str] = []
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
        skip = _redirection_skip_count(seg[i])
        if skip:
            redirects.extend(seg[i : i + skip])
            i += skip
            continue
        wrapper = _strip_quotes(seg[i]).rsplit("/", 1)[-1]
        if wrapper in _WRAPPER_OPTIONS:
            i = _after_wrapper_options(seg, i + 1, wrapper, redirects)
            if i < 0:
                return None
            continue
        if wrapper == "env":
            j = i + 1
            value_pending = False
            while j < len(seg):
                token = _strip_quotes(seg[j])
                skip = _redirection_skip_count(seg[j])
                if skip:
                    redirects.extend(seg[j : j + skip])
                    j += skip
                    continue
                if value_pending:
                    # The value of -u, -C or -S is the next non-redirect word.
                    value_pending = False
                    j += 1
                    continue
                if token.isdigit():
                    return "env", redirects + seg[i + 1 :], i
                if _is_assignment(seg[j]):
                    j += 1
                elif token.startswith("--"):
                    value_pending = token in {"--unset", "--chdir", "--split-string"}
                    j += 1
                elif token.startswith("-"):
                    for index, letter in enumerate(token[1:], 1):
                        if letter in "uCS":
                            value_pending = index == len(token) - 1
                            break
                    j += 1
                else:
                    break
            if j >= len(seg):
                return "env", redirects + seg[i + 1 :], i
            i = j
            continue
        break
    if i >= len(seg):
        return None

    cmd = _strip_quotes(seg[i]).rsplit("/", 1)[-1]
    return cmd, redirects + seg[i + 1 :], i


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


def _is_secrets_directory(path: str) -> bool:
    """True for the singular or plural secret directory and its contents."""
    clean = _strip_quotes(path).replace("\\", "/").lower()
    if not clean or clean == "-":
        return False
    folded = clean.replace("${home}", "~").replace("$home", "~")
    for directory in (".secret", ".secrets"):
        if folded in {f"~/{directory}", f"~/{directory}/", f"~/{directory}/*"}:
            return True
        if folded.startswith(f"~/{directory}/") or folded.startswith(f"~/{directory}*"):
            return True
        if f"/{directory}/" in folded or folded.endswith(f"/{directory}") or folded.endswith(f"/{directory}/*"):
            return True
    return False


def _is_known_secret_file(path: str) -> bool:
    clean = _strip_quotes(path).lower()
    if not clean or clean == "-":
        return False
    if _is_secrets_directory(clean):
        return True
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
    return [_strip_quotes(arg) for arg in _raw_without_redirects(args)]


def _raw_without_redirects(args: list[str]) -> list[str]:
    """Drop redirections, keeping each remaining word's quoting."""
    result = []
    index = 0
    while index < len(args):
        skip = _redirection_skip_count(args[index])
        if skip:
            index += skip
        else:
            result.append(args[index])
            index += 1
    return result


def _stdout_target(args: list[str]) -> str | None:
    destinations: dict[str, str | None] = {"1": None, "2": "/dev/stderr"}
    for index, token in enumerate(args[:-1]):
        raw = args[index + 1]
        target = "/dev/stderr" if _redirect_target_dynamic(raw) else _strip_quotes(raw)
        if token in {"&>", "&>>"}:
            destinations["1"] = destinations["2"] = target
            continue
        match = re.fullmatch(r"([0-9]*)(>&|<&|>>?|>\|)", token)
        if not match:
            continue
        spelling, operator = match.groups()
        descriptor = (spelling or ("0" if operator == "<&" else "1")).lstrip("0") or "0"
        if operator in {">&", "<&"}:
            # Bash's descriptor-less >&file redirects both output streams.
            if operator == ">&" and not spelling and not re.fullmatch(r"[0-9]+-?|\-", target):
                destinations["1"] = destinations["2"] = target
                continue
            if re.fullmatch(r"[0-9]+-?", target):
                source = target.rstrip("-").lstrip("0") or "0"
                target = destinations.get(source, "/dev/stderr")
                if _strip_quotes(raw).endswith("-"):
                    destinations[source] = "/dev/null"
            else:
                target = "/dev/null" if target == "-" else "/dev/stderr"
        destinations[descriptor] = target
    return destinations["1"]


_SECRET_FILTER_RE = re.compile(r"(?i)(?:key|token|secret|password)")


def _printenv_arg_is_secret(arg: str) -> bool:
    """True when a printenv operand names or globs a credential."""
    if not arg or arg.startswith("-"):
        return False
    return _is_secret_var_name(arg) or _SECRET_FILTER_RE.search(arg) is not None


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
        if names and not any(_printenv_arg_is_secret(name) for name in names):
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
        if target is not None:
            target = _normalized_path(target)
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
                dumped_files.add(target)
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
        if any(_normalized_path(path) in dumped_files for path in paths):
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
    fd_trimmed = re.sub(r"^\{[A-Za-z_][A-Za-z0-9_]*\}", "", token).lstrip("0123456789")
    if fd_trimmed in {"<", ">", ">>", "<>", ">|", ">&", "<&", "<<", "<<-", "<<<"}:
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


def _normalized_path(path: str) -> str:
    clean = os.path.normpath(_strip_quotes(path))
    if clean.startswith("//"):
        clean = clean[1:]
    return clean


def _sensitive_path(path: str) -> bool:
    clean = _normalized_path(path)
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
    # Compound commands can carry input redirects after their closing keyword.
    cmd, args = (found[0], found[1]) if found else ("", pipeline[index])
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
    operands += [
        args[i + 1]
        for i, token in enumerate(args[:-1])
        if re.fullmatch(r"(?:[0-9]+|\{[A-Za-z_][A-Za-z0-9_]*\})?(?:<|<>)", token)
    ]
    # Named file operands (e.g. dd's if=) and long options carry the same path.
    operands += [_strip_quotes(arg).split("=", 1)[1] for arg in args if "=" in arg and not _redirection_skip_count(arg)]
    paths = [_strip_quotes(arg) for arg in operands]
    sensitive = [path for path in paths if _sensitive_path(path) or _normalized_path(path) in dumped_files]
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


# Shell long options that take the next word, spelled with one or two dashes.
_SHELL_VALUE_OPTIONS = {"rcfile", "init-file", "emulate"}
# A literal first character that is not an option sign. Quotes, escapes,
# expansions, tildes, globs, braces and substitutions could make it one.
_SCRIPT_START = re.compile(r"""[^-+$`\\~{*?['"_]|'[^-+']|"[^-+"$`\\_]""")


def _shell_script(args: list[str]) -> list[str]:
    """Extract the script operand of a shell -c invocation.

    Every word before the script must be a plain literal word of letters,
    digits and dashes, so no expansion can add or hide an option. The first
    other word ends that region; it must start with a literal character that
    is not an option sign, or the script is unreadable. When an option holds
    `c`, that word and every plain non-option word before it are read as the
    script, since a plain word may be an option's operand or the script itself.
    """
    # Redirections may precede or sit among the options (`sh 2>/dev/null -c ...`).
    args = _raw_without_redirects(args)
    command = False
    operands = 0
    scripts: list[str] = []
    for index, word in enumerate(args):
        if not re.fullmatch(r"[A-Za-z0-9-]+", word):
            if operands or not _SCRIPT_START.match(word):
                return ["__UNDECIDABLE_SECRET_COMMAND__"]
            # The tokenizer cannot tell quote fragments of one word (`'pk'"ill -f w"`)
            # from separate words (`'env' _`), so the script is read both ways.
            for script in _script_words(args, index) + _script_words(args[index : index + 1], 0):
                if script not in scripts:
                    scripts.append(script)
            break
        pending = max(operands - 1, 0)
        if word.startswith("-"):
            # Every single-dash word counts, operands and long options (`-posix`)
            # included, so the reader can only over-report options and operands.
            command = command or (not word.startswith("--") and "c" in word)
            name = word.lstrip("-")
            if name in _SHELL_VALUE_OPTIONS:
                operands = max(pending, 1)
            else:
                operands = max(pending, 0 if word.startswith("--") else sum(letter in "oO" for letter in name))
        else:
            scripts.append(word)
            operands = pending
    return scripts if command else []


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


# Process kills are decided from the live process table (#12118). The text
# reader finds kill sites and refuses any shell construct that runs text it
# cannot read; the kill sites are then resolved against the live processes the
# agent depends on with procps' own selection, never predicted from text.
_KILL_COMMANDS = {"kill", "pkill", "killall"}
_PROCESS_SELECTORS = {"pgrep", "pidof"}
_PROCESS_SHELLS = {"bash", "sh", "dash", "zsh", "ksh"}
# Commands that print or look up their operands and never run them.
_PROCESS_DATA_COMMANDS = {
    "echo",
    "printf",
    "grep",
    "egrep",
    "fgrep",
    "type",
    "which",
    "whereis",
    "man",
    "help",
    "whatis",
    "apropos",
}
# A later word naming one of these may be a command another program runs.
_PROCESS_COMMAND_STARTS = _KILL_COMMANDS | _PROCESS_SELECTORS | _PROCESS_SHELLS | {"eval", "xargs", "env"}
_SELF_PID_EXPANSION = re.compile(r"\$(?:\$|\{\$\}|\{?PPID\b|\{?BASHPID\b)")
_SELF_MATCH = "a process kill would reach the agent's own shell, its harness or an ancestor"
# The agent's shell holds the command inside a harness wrapper the guard cannot know.
_WRITTEN_SCRIPT = (
    "the command writes a script and runs it or makes it executable, so the guard cannot read it; "
    "write the script in one command and run it in the next"
)
_FULL_MATCH = "full-command-line process kills can match the agent's own shell, whose command line holds the command"
_PARAMETER = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?-)([^}$`\\]*))?\}|([A-Za-z_][A-Za-z0-9_]*))")
_MAX_WORD_CANDIDATES = 16
# Tools that write every file operand, and tools that write only their last operand.
_FILE_WRITERS = {"tee", "touch"}
# Launchers that run their command under other user or group IDs.
_CREDENTIAL_LAUNCHERS = {"sudo", "doas", "su", "runuser", "setpriv", "pkexec", "sg", "newgrp", "setuidgid", "chpst"}
# Programs that only read, copy or describe their file operands, never run them.
_FILE_TOOLS = {
    "cp",
    "mv",
    "install",
    "ln",
    "rm",
    "chmod",
    "chown",
    "chgrp",
    "touch",
    "cat",
    "ls",
    "head",
    "tail",
    "wc",
    "diff",
    "cmp",
    "stat",
    "file",
    "mkdir",
    "rmdir",
    "readlink",
    "realpath",
    "basename",
    "dirname",
    "du",
    "md5sum",
    "sha1sum",
    "sha256sum",
    "tar",
    "gzip",
    "gunzip",
    "zip",
    "unzip",
    "git",
    "sort",
    "uniq",
    "cut",
    "tr",
    "jq",
    "sed",
    "awk",
    "tee",
    "less",
    "more",
}
_FILE_COPIERS = {"cp", "mv", "install", "ln"}
_SUBSTITUTION_MARKER = re.compile(r"__GUARD_SUBSTITUTION_\d+__+")
_PGREP_LONG_NAME_WARNING = (
    "pgrep: pattern that searches for process name longer than 15 characters will result in zero matches\n"
    "Try `pgrep -f' option to match against the complete command line.\n"
)
# procps 4.0.4 signal_name_to_number(): its table, aliases and specials, compared case-insensitively.
_PROCPS_SIGNALS = {
    "ABRT",
    "ALRM",
    "BUS",
    "CHLD",
    "CONT",
    "FPE",
    "HUP",
    "ILL",
    "INT",
    "KILL",
    "PIPE",
    "POLL",
    "PROF",
    "PWR",
    "QUIT",
    "SEGV",
    "STKFLT",
    "STOP",
    "SYS",
    "TERM",
    "TRAP",
    "TSTP",
    "TTIN",
    "TTOU",
    "URG",
    "USR1",
    "USR2",
    "VTALRM",
    "WINCH",
    "XCPU",
    "XFSZ",
    "CLD",
    "IO",
    "IOT",
    "RTMIN",
    "EXIT",
    "NULL",
}
# procps 4.0.4 pgrep/pkill getopt_long tables.
_PGREP_SHORT = "lad:vwLF:cfinoxP:O:AHg:s:u:U:G:t:r:Vh"
_PKILL_SHORT = "eq:LF:cfinoxP:O:AHg:s:u:U:G:t:r:Vh"
_PGREP_LONG = [
    "signal=",
    "ignore-ancestors",
    "require-handler",
    "count",
    "cgroup=",
    "delimiter=",
    "list-name",
    "list-full",
    "full",
    "pgroup=",
    "group=",
    "ignore-case",
    "newest",
    "oldest",
    "older=",
    "parent=",
    "session=",
    "terminal=",
    "euid=",
    "uid=",
    "inverse",
    "lightweight",
    "exact",
    "pidfile=",
    "logpidfile",
    "echo",
    "ns=",
    "nslist=",
    "queue=",
    "runstates=",
    "help",
    "version",
]
# Options whose meaning is the same for the agent's shell and its stand-in, and
# for the live ancestors when the command runs: name, case, inversion and IDs.
_PGREP_SELECTION = {"-i": "-i", "--ignore-case": "-i", "-x": "-x", "--exact": "-x", "-v": "-v", "--inverse": "-v"}
_PGREP_SELECTION_VALUES = {"-u": "-u", "--euid": "-u", "-U": "-U", "--uid": "-U", "-G": "-G", "--group": "-G"}
# Options that only shape output or the signal sent, never the selection.
_PGREP_OUTPUT = {"--signal", "-e", "--echo", "-q", "--queue", "-c", "--count", "-l", "--list-name"}
_PGREP_OUTPUT |= {"-a", "--list-full", "-d", "--delimiter"}
_XARGS_VALUE_LONGS = {
    "--arg-file",
    "--delimiter",
    "--max-lines",
    "--max-args",
    "--max-procs",
    "--max-chars",
    "--process-slot-var",
}


class _Unresolvable(Exception):
    """The live process table cannot answer for this command."""


class _ProcessFacts:
    """Kill sites, selectors and unreadable parts found in one invocation."""

    def __init__(self, command: str, cwd: str | None = None, prior: _ProcessFacts | None = None) -> None:
        self.command = command
        # Effects found anywhere in the previous reading, at any depth: they apply
        # to the whole invocation, so the next reading decides with them.
        self.prior = prior
        self.ifs_set = False
        self.echo_rebound = False
        self.launched: list[str] = []
        self.executable: set[str] = set()
        self.startup_unknown = False
        self.credential_change = False
        # Copies of executables, and files whose content the command writes.
        self.executable_copies: set[str] = set()
        self.content_written: set[str] = set()
        self.limit = False
        self.opaque = False
        self.unresolved = False
        self.exec_names: set[str] = set()
        self.calls: list[tuple[str, tuple[str, ...], bool]] = []
        # The raw value words assigned to each parameter, or None when one is not a plain assignment.
        self.assignments: dict[str, list[str] | None] = {}
        self._documents: dict[str, list[tuple[str, bool]]] | None = None
        self._may_set_ifs: bool | None = None
        # Scripts the command runs: (word, read by a shell), and what it writes.
        self.scripts: list[tuple[str, bool]] = []
        self.programs: list[str] = []
        self.renames = False
        self.written: set[str] = set()
        self.unknown_write = False
        self.directories: set[str] = set()
        self.unknown_directory = False
        self.cwd = cwd or os.getcwd()

    def may_set_ifs(self) -> bool:
        """Whether the command can change IFS, which splits unquoted expansions.

        It can when its quote-removed text names IFS, or when one of Bash's
        assigning forms targets a name the reader cannot read: `printf -v`, `read`,
        `mapfile`, `readarray`, `getopts`, the declaration builtins, `let`, and
        arithmetic with an expansion in it.
        """
        if self._may_set_ifs is None:
            self._may_set_ifs = _may_set_ifs(self.command) or bool(self.prior and self.prior.ifs_set)
        return self._may_set_ifs

    def effects(self) -> tuple[object, ...]:
        """The effects a later reading depends on, to detect a fixpoint."""
        return (self.ifs_set, self.echo_rebound)

    def documents(self) -> dict[str, list[tuple[str, bool]]]:
        if self._documents is None:
            self._documents = _heredoc_inputs(self.command)
        return self._documents

    def parameter_words(self, name: str) -> list[str] | None:
        """The words a parameter can hold: its plain assignments, or the inherited environment.

        Any other spelling of the name in the command (`read K`, `printf -v K`,
        `for K in`) may assign it some other way, so it cannot be resolved.
        """
        # A name glued to an option cluster (`printf -vK`) is a spelling too.
        named = len(re.findall(rf"(?:(?<![A-Za-z0-9_])|(?<=-)[A-Za-z]*){name}(?![A-Za-z0-9_])", self.command))
        expanded = len(re.findall(rf"\$\{{?{name}(?![A-Za-z0-9_])", self.command))
        assigned = self.assignments.get(name, [])
        if assigned is None or named != expanded + len(assigned):
            return None
        return assigned or [shlex.quote(os.environ.get(name, ""))]

    def parameter(self, name: str, depth: int) -> list[str] | None:
        """Every value a parameter can hold, or None when one is unknown."""
        words = self.parameter_words(name)
        values: list[str] = []
        for word in words or []:
            candidates = _word_candidates(word, self, depth + 1)
            if candidates is None:
                return None
            values += candidates
        return values if words is not None else None


def _process_block_msg(reason: str) -> str:
    return (
        f"BLOCKED by guard-secret-print (#M-5): {reason}.\n\n"
        "Kill exact numeric PIDs read in an earlier command, or stop a harness background "
        "task with the harness's own stop tool.\n"
    )


def _word_parts(word: str) -> list[tuple[str, str]] | None:
    """Split a shell word into ("lit", text), ("param", spelling) and ("dyn", "") parts.

    Quote removal is applied; a parameter's spelling keeps a leading quote mark
    when it was double-quoted. None means the word's quoting is malformed.
    """
    parts: list[tuple[str, str]] = []
    index = 0

    def parameter(quoted: bool) -> int:
        match = _PARAMETER.match(word, index)
        if match is None:
            # A special parameter (`$$`, `$1`), a complex `${...}` or a lone `$`.
            parts.append(("dyn", ""))
            if word.startswith("${", index):
                end = word.find("}", index)
                return end + 1 if end >= 0 else len(word)
            following = word[index + 1 : index + 2]
            return index + 2 if following and following not in "'\"" else index + 1
        parts.append(("param", ('"' if quoted else "") + match.group(0)))
        return match.end()

    while index < len(word):
        char = word[index]
        marker = _SUBSTITUTION_MARKER.match(word, index)
        if marker:
            # A hidden command substitution, quoted or not.
            parts.append(("dyn", ""))
            index = marker.end()
        elif char == "'":
            end = word.find("'", index + 1)
            if end < 0:
                return None
            parts.append(("lit", word[index + 1 : end]))
            index = end + 1
        elif char == '"':
            index += 1
            while index < len(word) and word[index] != '"':
                marker = _SUBSTITUTION_MARKER.match(word, index)
                if marker:
                    parts.append(("dyn", ""))
                    index = marker.end()
                elif word[index] == "$":
                    index = parameter(True)
                elif word[index] == "`":
                    parts.append(("dyn", ""))
                    index += 1
                elif word[index] == "\\" and index + 1 < len(word) and word[index + 1] in '$`"\\\n':
                    parts.append(("lit", word[index + 1] if word[index + 1] != "\n" else ""))
                    index += 2
                else:
                    parts.append(("lit", word[index]))
                    index += 1
            if index >= len(word):
                return None
            index += 1
        elif char == "\\":
            if index + 1 >= len(word):
                return None
            parts.append(("lit", word[index + 1] if word[index + 1] != "\n" else ""))
            index += 2
        elif char == "$":
            index = parameter(False)
        elif (
            char in "`*?"
            or (char == "~" and index == 0)
            or (char == "[" and "]" in word[index + 1 :])
            or (char == "{" and re.match(r"\{[^}]*(?:,|\.\.)[^}]*\}", word[index:]))
        ):
            # Substitutions, globs, tildes and brace expansions.
            parts.append(("dyn", ""))
            index += 1
        else:
            parts.append(("lit", char))
            index += 1
    return parts


def _shell_word_value(word: str) -> str | None:
    """Return a word after Bash quote removal, or None when an expansion could change it."""
    parts = _word_parts(word)
    if parts is None or any(kind != "lit" for kind, _ in parts):
        return None
    return "".join(text for _, text in parts)


def _word_candidates(word: str, facts: _ProcessFacts, depth: int = 0) -> list[str] | None:
    """Every value a word can take, expanding simple parameters; None when unknown."""
    parts = _word_parts(word)
    if parts is None or depth > 4:
        return None
    candidates = [""]
    for kind, text in parts:
        if kind == "dyn":
            return None
        if kind == "lit":
            candidates = [candidate + text for candidate in candidates]
            continue
        quoted = text.startswith('"')
        match = _PARAMETER.match(text.lstrip('"'))
        assert match is not None
        values = facts.parameter(match.group(1) or match.group(4), depth)
        if values is None:
            return None
        if match.group(2):
            default = _shell_word_value(match.group(3) or "")
            if default is None:
                return None
            values = [value or default for value in values] if match.group(2) == ":-" else [*values, default]
        # Unquoted expansions are split at IFS characters and globbed.
        if not quoted and (facts.may_set_ifs() or any(re.search(r"[\s*?[]", value) for value in values)):
            return None
        candidates = [candidate + value for candidate in candidates for value in values]
        if len(candidates) > _MAX_WORD_CANDIDATES:
            return None
    return candidates


def _splits(word: str) -> bool:
    """Whether a word holds an unquoted expansion or substitution, which IFS can split."""
    quote = ""
    index = 0
    while index < len(word):
        char = word[index]
        if quote == "'":
            quote = "" if char == "'" else quote
        elif char == "\\":
            index += 1
        elif char in "'\"" and (not quote or char == quote):
            quote = "" if quote else char
        elif not quote and (char in "$`" or _SUBSTITUTION_MARKER.match(word, index)):
            return True
        index += 1
    return False


def _command_names(word: str, facts: _ProcessFacts, depth: int = 0) -> list[str] | None:
    """The program names a command word can run, or None when it cannot be known."""
    candidates = _word_candidates(word, facts)
    if candidates is not None:
        if "" in candidates:
            return None
        # A word ending in a slash names a directory, which runs nothing.
        return sorted({candidate.rsplit("/", 1)[-1] for candidate in candidates} - {""})
    parts = _word_parts(word)
    if parts is None or depth > 4:
        return None
    if len(parts) == 1 and parts[0][0] == "param" and parts[0][1].startswith('"'):
        # A lone quoted parameter names whatever program each of its assigned words
        # names. Unquoted, a partly unknown value could split into other words.
        match = _PARAMETER.match(parts[0][1].lstrip('"'))
        assert match is not None
        words = None if match.group(2) else facts.parameter_words(match.group(1) or match.group(4))
        names: set[str] = set()
        for assigned in words or []:
            found = _command_names(assigned, facts, depth + 1)
            if found is None:
                return None
            names.update(found)
        return sorted(names) if words is not None else None
    # A path whose last component is literal names its program whatever the
    # directory, provided no unquoted expansion can split the word.
    slashes = [index for index, (kind, text) in enumerate(parts) if kind == "lit" and "/" in text]
    if not slashes or any(kind != "lit" for kind, _ in parts[slashes[-1] + 1 :]) or _splits(word):
        return None
    name = parts[slashes[-1]][1].rsplit("/", 1)[-1] + "".join(text for _, text in parts[slashes[-1] + 1 :])
    return [name] if name else []


def _xargs_target(args: list[str]) -> list[str]:
    """Return the command words xargs runs, after its own options."""
    words = _raw_without_redirects(args)
    index = 0
    while index < len(words):
        word = _strip_quotes(words[index])
        if word == "--":
            return words[index + 1 :]
        if word in _XARGS_VALUE_LONGS:
            index += 2
        elif word.startswith("--") or word == "-":
            index += 1
        elif word.startswith("-"):
            index += 1
            # A value letter ends a short cluster; at its end the value is the next word.
            for position, letter in enumerate(word[1:], 1):
                if letter in "adEILnPs":
                    index += position == len(word) - 1
                    break
        else:
            return words[index:]
    return []


def _script_operand(args: list[str]) -> str | None:
    """Return the script-file word of a shell without -c, None when it reads standard
    input, or "" when it only reports and runs nothing (`--version`, `--help`)."""
    pending = 0
    for word in _raw_without_redirects(args):
        value = _shell_word_value(word)
        if value in {"--version", "--help"}:
            return ""
        if value is None:
            return word
        if pending:
            pending -= 1
        elif value[:1] in {"-", "+"} and value not in {"-", "+", "--"}:
            name = value.lstrip("-+")
            if not value.startswith("--") and "s" in name:
                return None
            if value.startswith("-") and not value.startswith("--") and "n" in name:
                # noexec: the shell only parses its script.
                return ""
            if name in _SHELL_VALUE_OPTIONS:
                pending = 1
            elif not value.startswith("--"):
                pending = sum(letter in "oO" for letter in name)
        elif value != "--":
            return None if value in {"-", "+"} or value.startswith(("/dev/", "/proc/")) else word
    return None


def _stdin_scripts(args: list[str], facts: _ProcessFacts) -> list[str] | None:
    """Scripts a shell reads from its here-document or here-string, or None if not readable."""
    scripts: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        operator = re.match(r"\d*(<<<|<<-?)", token)
        if operator is None:
            index += 1
            continue
        word = token[operator.end() :] or (args[index + 1] if index + 1 < len(args) else "")
        index += 1 if token[operator.end() :] else 2
        value = _shell_word_value(word)
        if value is None:
            return None
        if operator.group(1) == "<<<":
            scripts.append(value)
            continue
        documents = facts.documents().get(value)
        if not documents:
            return None
        for body, quoted in documents:
            # An unquoted delimiter expands the body before the shell reads it.
            if not quoted and re.search(r"[$`\\]", body):
                return None
            scripts.append(body)
    return scripts


_SHELL_OPERATORS = sorted(
    {"<<<", "<<-", "<<", ">>", "<&", ">&", "&>>", "&>", ">|", "<>", "&&", "||", "|&", ";;", "|", "&", ";", "(", ")"}
    | {"<", ">"},
    key=len,
    reverse=True,
)


def _process_tokens(text: str) -> list[str]:
    """Split shell text into quote-preserving words and operators, as Bash does.

    Unlike the shared lexer, a quote may open inside a word (`K='a b'`), and a
    `${...}` expansion stays one word. Raises ValueError on an unclosed quote.
    """
    tokens: list[str] = []
    word: list[str] = []
    quote = ""
    index = 0

    def flush() -> None:
        if word:
            tokens.append("".join(word))
            word.clear()

    while index < len(text):
        char = text[index]
        if quote:
            word.append(char)
            if quote == '"' and char == "\\" and index + 1 < len(text):
                word.append(text[index + 1])
                index += 1
            elif char == quote:
                quote = ""
            index += 1
        elif char == "\\":
            if text.startswith("\\\n", index):
                index += 2
                continue
            word.append(text[index : index + 2])
            index += 2
        elif char in "'\"":
            quote = char
            word.append(char)
            index += 1
        elif text.startswith("${", index):
            end = text.find("}", index)
            if end < 0:
                raise ValueError("unclosed parameter expansion")
            word.append(text[index : end + 1])
            index = end + 1
        elif text.startswith("$(", index):
            # An arithmetic expansion or a substitution the caller left in place.
            depth, end = 0, index + 1
            while end < len(text):
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                if depth == 0:
                    break
                end += 1
            if depth:
                raise ValueError("unclosed substitution")
            word.append(text[index : end + 1])
            index = end + 1
        elif char in " \t":
            flush()
            index += 1
        elif char == "\n":
            flush()
            tokens.append("\n")
            index += 1
        elif char == "(" and "".join(word).endswith("="):
            # An array assignment's element list belongs to its word.
            depth, end, inner = 0, index, ""
            while end < len(text):
                if inner:
                    inner = "" if text[end] == inner else inner
                elif text[end] in "'\"":
                    inner = text[end]
                else:
                    depth += {"(": 1, ")": -1}.get(text[end], 0)
                    if depth == 0:
                        break
                end += 1
            if depth:
                raise ValueError("unclosed array assignment")
            word.append(text[index : end + 1])
            index = end + 1
        elif char in ";&|()<>":
            # Digits right before a redirection name its file descriptor (`2>`).
            prefix = "".join(word) if word and "".join(word).isdigit() and char in "<>" else ""
            if prefix:
                word.clear()
            flush()
            operator = next(op for op in _SHELL_OPERATORS if text.startswith(op, index))
            tokens.append(prefix + operator)
            index += len(operator)
        else:
            word.append(char)
            index += 1
    if quote:
        raise ValueError("unclosed quote")
    flush()
    return tokens


_CASE_OPENERS = {"do", "then", "else", "{", "!", "time"}
# Builtins that run or bind shell text; a path never reaches them.
_TEXT_BUILTINS = {"eval", "alias", "trap", "hash", "enable", "source", "."}


def _process_pipelines(text: str) -> list[list[list[str]]]:
    """Group `_process_tokens` into pipelines of simple-command segments."""
    pipelines: list[list[list[str]]] = []
    pipeline: list[list[str]] = []
    segment: list[str] = []
    # Inside `case WORD in`, patterns up to `)` are not commands.
    case_state = ""
    for token in _process_tokens(text):
        if case_state == "word":
            case_state = "patterns" if token == "in" else "word"
            continue
        if case_state == "patterns":
            if token == "esac":
                case_state = ""
            elif token == ")":
                case_state = "body"
            continue
        if case_state == "body" and token in {";;", ";&", ";;&"}:
            case_state = "patterns"
            token = ";"
        if token == "case" and set(segment) <= _CASE_OPENERS:
            case_state = "word"
            continue
        if case_state == "body" and not segment and token == "esac":
            case_state = ""
            continue
        if token in {"|", "|&"}:
            if segment:
                pipeline.append(segment)
            segment = []
        elif token in SEPARATORS or token in {"(", ")", ";;"} or _is_command_brace(token, segment):
            if segment:
                pipeline.append(segment)
            if pipeline:
                pipelines.append(pipeline)
            pipeline, segment = [], []
        else:
            segment.append(token)
    if segment:
        pipeline.append(segment)
    if pipeline:
        pipelines.append(pipeline)
    return pipelines


def _segment_process_facts(words: list[str], facts: _ProcessFacts, depth: int, *, fed: bool = False) -> None:
    if depth >= 12:
        facts.limit = True
        return
    # `env -S` splits a string into a command the reader never sees.
    for index, word in enumerate(words):
        if _shell_word_value(word) not in {"env", "/usr/bin/env", "/bin/env"}:
            continue
        for option in words[index + 1 :]:
            if _is_assignment(option):
                continue
            values = _word_candidates(option, facts)
            if values is None and _command_names(option, facts) is not None:
                # A path with a literal program name is the command, not an option.
                break
            if values is None or any(re.match(r"-[^-]*S|--s", value) for value in values):
                facts.opaque = True
            if values is None or not any(value.startswith("-") for value in values):
                break
    found = _command_at(words)
    if found is None:
        # Assignments alone, or a command `_command_at` only looks up.
        _record_assigning(words, len(words), [], facts)
        return
    cmd, args, index = found
    if cmd == "__UNDECIDABLE_SECRET_COMMAND__":
        facts.limit = True
        return
    names = _command_names(words[index], facts)
    if names is None:
        facts.unresolved = True
        return
    leading = [_shell_word_value(word) for word in words[:index] if not _is_assignment(word)]
    if "exec" in leading:
        # exec keeps the shell's PID under the new program's name, and a launcher it
        # runs (`exec chrt ... sleep`) may exec again: every later word may name it.
        for word in words[leading.index("exec") + 1 :]:
            value = _shell_word_value(word)
            if value is None:
                facts.unresolved = True
            elif value and not value.startswith("-") and not value.isdigit():
                facts.exec_names.add(value.rsplit("/", 1)[-1])
        if len(facts.exec_names) > _MAX_WORD_CANDIDATES:
            facts.unresolved = True
    _record_assigning(words, index, names, facts)
    values = _word_candidates(words[index], facts)
    if "/" in words[index] or any("/" in value for value in values or []):
        facts.scripts.append((words[index], False))
    else:
        # A bare name runs whatever PATH finds, which may be a file this command writes.
        facts.programs.extend(names)
    for name in names:
        if name in _TEXT_BUILTINS and "/" in words[index]:
            name = ""
        if name in {"alias", "enable", "hash"}:
            facts.echo_rebound = True
        if name != cmd and (name in _WRAPPER_OPTIONS or name in {"env", "xargs"}):
            # A spliced or expanded wrapper word, read again as its literal name.
            _segment_process_facts([*words[:index], shlex.quote(name), *words[index + 1 :]], facts, depth + 1, fed=fed)
        else:
            _program_process_facts(name, words, index, args, facts, depth, fed)


def _record_assigning(words: list[str], index: int, names: list[str], facts: _ProcessFacts) -> None:
    """Note an assignment to IFS, or to a name the reader cannot read, by any resolved form."""
    targets = [word.split("=", 1)[0] for word in words[:index] if _is_assignment(word)]
    if words and _shell_word_value(words[0]) in {"for", "select"} and len(words) > 1:
        targets.append(words[1])
    for name in names:
        rest = _raw_without_redirects(words[index + 1 :])
        if name == "printf":
            # printf assigns through -v NAME and through each %n conversion's argument.
            position = 0
            first = _word_candidates(rest[0], facts) if rest else [""]
            if first is None:
                # It could be -v with a name the reader cannot read.
                facts.ifs_set = facts.startup_unknown = True
                continue
            glued = [value[2:] for value in first if value.startswith("-v") and len(value) > 2]
            if glued or "-v" in first:
                targets += glued or rest[1:2]
                position = 1 if glued else 2
            elif first == ["--"]:
                position = 1
            formats = _word_candidates(rest[position], facts) if position < len(rest) else [""]
            if formats is None or any(re.search(r"%[^%a-zA-Z]*n", value) for value in formats):
                targets += rest[position + 1 :]
        elif name in _ASSIGNING_BUILTINS:
            options = [
                _shell_word_value(word) or "" for word in rest if (_shell_word_value(word) or "x").startswith("-")
            ]
            if any("n" in option.lstrip("-") for option in options if name in {"declare", "typeset", "local"}):
                # A nameref (`declare -n R=IFS`) assigns through another name.
                facts.ifs_set = True
            targets += [word.split("=", 1)[0] for word in rest if not (_shell_word_value(word) or "x").startswith("-")]
    builtin = bool(set(names) & (_ASSIGNING_BUILTINS | {"printf"}))
    for target in targets:
        value = _shell_word_value(target)
        if value is None or value == "IFS":
            facts.ifs_set = True
        if builtin and value in {None, "BASH_ENV", "ENV"}:
            # A startup file Bash reads, set by a form whose value the reader does not track.
            facts.startup_unknown = True


def _program_process_facts(
    name: str, words: list[str], index: int, args: list[str], facts: _ProcessFacts, depth: int, fed: bool
) -> None:
    if name == "xargs":
        target = _xargs_target(args)
        if target:
            # The target is shorter than the segment, so a long xargs chain ends.
            _segment_process_facts(target, facts, depth, fed=True)
    elif name in _KILL_COMMANDS or name in _PROCESS_SELECTORS:
        facts.calls.append((name, tuple(_raw_without_redirects(args)), fed))
    elif name in _PROCESS_SHELLS or name in {"source", "."}:
        scripts = _shell_script(args) if name in _PROCESS_SHELLS else []
        if not scripts:
            operand = _script_operand(args)
            if operand == "":
                return
            if operand is None:
                scripts = _stdin_scripts(args, facts) or []
                facts.opaque = facts.opaque or not scripts
            else:
                facts.scripts.append((operand, True))
        for script in scripts:
            _collect_process_facts(script, facts, depth + 1)
    elif name in {"eval", "alias", "trap"}:
        # eval runs its words joined by spaces; alias stores each NAME=TEXT, and
        # trap its first operand, as shell text that runs later.
        words = _raw_without_redirects(args)
        if name == "trap":
            words = [word for word in words if not (_shell_word_value(word) or "").startswith("-")][:1]
        candidates = [_word_candidates(word, facts) for word in words]
        if any(values is None for values in candidates):
            facts.opaque = True
            return
        if name == "eval":
            scripts = [""]
            for values in candidates:
                scripts = [f"{script} {value}".lstrip() for script in scripts for value in values or []]
                if len(scripts) > _MAX_WORD_CANDIDATES:
                    facts.opaque = True
                    return
        else:
            scripts = [value.split("=", 1)[-1] for values in candidates for value in values or []]
        for script in scripts:
            _collect_process_facts(script, facts, depth + 1)
    elif name in {"hash", "enable"}:
        # Both can bind a command name to another program.
        facts.opaque = True
    elif name not in _PROCESS_DATA_COMMANDS:
        # Another program may run a later word as a command (`setsid pkill`, `find -exec`),
        # including a path to an executable file this command rewrites.
        if name not in _FILE_TOOLS:
            facts.launched.extend(words[index + 1 :])
        for later in range(index + 1, len(words)):
            starts = _PROCESS_COMMAND_STARTS - (_TEXT_BUILTINS if "/" in words[later] else set())
            if set(_command_names(words[later], facts) or ()) & starts:
                _segment_process_facts(words[later:], facts, depth + 1, fed=fed)


def _record_assignments(executable: str, facts: _ProcessFacts) -> None:
    """Record literal parameter assignments, from plain words and export-style builtins."""
    for pipeline in _process_pipelines(_decode_ansi_c_quotes(executable)):
        for segment in pipeline:
            words = [word for word in segment if word not in {"!", "{", "(", "then", "do", "else"}]
            index = 0
            while index < len(words) and _is_assignment(words[index]):
                index += 1
            assigned = words[:index]
            if index < len(words) and _shell_word_value(words[index]) in {
                "export",
                "local",
                "declare",
                "typeset",
                "readonly",
            }:
                for word in words[index + 1 :]:
                    if _is_assignment(word):
                        assigned.append(word)
                    elif not re.fullmatch(r"-[xgr]+", _shell_word_value(word) or ""):
                        # Arrays, namerefs and computed names are not literal assignments.
                        for other in words[index + 1 :]:
                            facts.assignments[(_shell_word_value(other) or "").split("=", 1)[0]] = None
                        break
            for word in assigned:
                key, raw = word.split("=", 1)
                known = facts.assignments.get(key, [])
                facts.assignments[key] = None if known is None else [*known, raw]


def _effect_names(word: str, facts: _ProcessFacts) -> list[str] | None:
    """File names a word can denote: its values, or a literal last path component."""
    values = _word_candidates(word, facts)
    if values is not None:
        return [os.path.normpath(value) for value in values]
    names = _command_names(word, facts)
    return names or None


def _record_effects(pipelines: list[list[list[str]]], facts: _ProcessFacts) -> None:
    """Record the files a command writes, the directories it enters and its startup scripts."""

    def write(word: str, *, content: bool = True) -> None:
        value = _shell_word_value(word)
        if value is not None and re.fullmatch(r"/dev/(?:null|zero|tty|stdout|stderr|fd/\d+)", os.path.normpath(value)):
            # A device holds no script.
            return
        if content:
            facts.content_written.update(os.path.basename(name) for name in _effect_names(word, facts) or [""])
        if _under_proc(word, facts):
            # A process's name or attributes, such as /proc/$$/comm.
            facts.renames = True
        names = _effect_names(word, facts)
        if names is None:
            facts.unknown_write = True
        else:
            facts.written.update(os.path.basename(name) for name in names)

    for segment in (segment for pipeline in pipelines for segment in pipeline):
        values = [_shell_word_value(word) for word in segment]
        # Every program name each word can take, through quoting and parameters
        # (`"$P"` for tee): a word that may be one of several names counts as each.
        programs = [
            (index, name)
            for index, word in enumerate(segment)
            for name in sorted(set(_command_names(word, facts) or ()))
        ]
        for index, word in enumerate(segment[:-1]):
            if re.fullmatch(r"\d*(?:>|>>|>\||&>|&>>|<>)", word):
                write(segment[index + 1])
        for index, program in programs:
            # A word the reader cannot read counts as an operand, never as an option.
            operands = [word for word in segment[index + 1 :] if not (_shell_word_value(word) or "").startswith("-")]
            if program in {"tee", "touch"}:
                for word in operands:
                    write(word)
            elif program in {"cp", "mv", "install", "ln"} and operands:
                write(operands[-1], content=False)
                if program == "ln" and any(_under_proc(source, facts) for source in operands[:-1]):
                    # A link into /proc makes later writes through it renames.
                    facts.renames = True
                # A copy, move or link of an executable keeps its execute permission.
                for source in operands[:-1]:
                    paths = _effect_names(source, facts)
                    if paths is None or any(_is_executable(path, facts) for path in paths):
                        target = _effect_names(operands[-1], facts)
                        facts.executable_copies.update(os.path.basename(name) for name in target or [""])
            elif program == "dd":
                for word in segment[index + 1 :]:
                    if (_shell_word_value(word) or "of=").startswith("of="):
                        write(word.split("=", 1)[-1])
            elif program in {"sed", "perl"} and any(
                re.fullmatch(r"-[A-Za-z]*i.*|--in-place.*", value or "-i") for value in values[index + 1 :]
            ):
                for word in operands:
                    write(word)
            elif program in {"curl", "wget"}:
                for flag, target in zip(values[index + 1 :], segment[index + 2 :], strict=False):
                    if flag in {"-o", "--output", "-O", "--output-document"}:
                        write(target)
                if any(value in {"-O", "--remote-name", "-J"} for value in values[index + 1 :]) or (
                    program == "wget" and "-O" not in values
                ):
                    facts.unknown_write = True
        if {name for _, name in programs} & _CREDENTIAL_LAUNCHERS:
            facts.credential_change = True
        for index, program in programs:
            if program in {"chmod", "install"}:
                for word in segment[index + 1 :]:
                    names = _effect_names(word, facts)
                    facts.executable.update(os.path.basename(name) for name in names or [])
                    if names is None:
                        facts.executable.add("")
        # cd behind a wrapper or control word (`builtin cd`, `if cd ...`) still moves.
        moves = [index for index, program in programs if program in {"cd", "pushd", "popd"}]
        if any(program == "popd" for _, program in programs):
            facts.unknown_directory = True
        if moves:
            targets = [word for word in segment[moves[0] + 1 :] if not (_shell_word_value(word) or "x").startswith("-")]
            names = _word_candidates(targets[0], facts) if targets else [os.environ.get("HOME", "")]
            if targets and _under_proc(targets[0], facts):
                # Relative writes there rename processes.
                facts.renames = True
            if names is None:
                facts.unknown_directory = True
            else:
                facts.directories.update(os.path.join(facts.cwd, name) for name in names)
        for word in segment:
            if _is_assignment(word) and word.split("=", 1)[0] in {"BASH_ENV", "ENV"}:
                facts.scripts.append((word.split("=", 1)[1], True))


def _is_executable(path: str, facts: _ProcessFacts) -> bool:
    candidate = path if os.path.isabs(path) else os.path.join(facts.cwd, path)
    return os.path.isfile(candidate) and os.access(candidate, os.X_OK)


def _under_proc(word: str, facts: _ProcessFacts) -> bool:
    """Whether a path word, after quote removal and known parameters, lies under /proc."""
    parts = _word_parts(word) or []
    prefix = ""
    for kind, text in parts:
        if kind == "lit":
            prefix += text
            continue
        values = _word_candidates('"' + text.lstrip('"') + '"', facts) if kind == "param" else None
        if values is None or len(values) != 1:
            # An unknown part decides nothing once a fixed top directory is known;
            # before that, it could lead under /proc.
            fixed = prefix.startswith("/") and "/" in prefix[1:]
            return not fixed or os.path.normpath(prefix).startswith("/proc")
        prefix += values[0]
    if not prefix.startswith("/") and facts.unknown_directory:
        return True
    normalized = os.path.normpath(os.path.join(facts.cwd, prefix)) if prefix else facts.cwd
    return normalized == "/proc" or normalized.startswith("/proc/") or (not prefix and facts.cwd.startswith("/proc"))


def _script_reason(facts: _ProcessFacts) -> str | None:
    """Check each script the command runs: refuse one it writes or creates, read one it does not."""
    if any(name in facts.written for name in facts.programs):
        return _WRITTEN_SCRIPT
    if facts.renames and facts.calls:
        return "the command may rename a process through /proc beside a kill, which the guard cannot follow"
    if facts.startup_unknown and (facts.written or facts.unknown_write):
        return _WRITTEN_SCRIPT
    copies = facts.executable_copies
    rewritten_copy = (facts.content_written & copies) - {""}
    if facts.written & facts.executable or (facts.written and "" in facts.executable) or rewritten_copy:
        # A file the command writes and makes executable can run by any route:
        # a launcher, PATH, or a program's hook such as .git/hooks.
        return _WRITTEN_SCRIPT
    for word in facts.launched:
        for name in _effect_names(word, facts) or []:
            if os.path.basename(name) in facts.written and os.path.isfile(name) and os.access(name, os.X_OK):
                return _WRITTEN_SCRIPT
    seen: set[tuple[str, bool]] = set()
    while facts.scripts:
        word, by_shell = facts.scripts.pop()
        if (word, by_shell) in seen:
            continue
        seen.add((word, by_shell))
        names = _effect_names(word, facts)
        if names is None or any(os.path.basename(name) in facts.written for name in names):
            return _WRITTEN_SCRIPT
        values = _word_candidates(word, facts)
        if by_shell and facts.unknown_write:
            # A write to an unknown path could be this script.
            return _WRITTEN_SCRIPT
        for value in values or []:
            directories = {facts.cwd, *facts.directories}
            paths = [value] if os.path.isabs(value) else [os.path.join(directory, value) for directory in directories]
            existing = [path for path in paths if os.path.isfile(path)]
            if not existing:
                # Not there yet, so this command would have to create it. Its kill text
                # comes from the command text, or from data or another language's code.
                if not facts.unknown_directory and _mentions_process_kill(facts.command):
                    return _WRITTEN_SCRIPT
                continue
            for path in existing:
                text = _shell_script_text(path, by_shell)
                if text is not None and not by_shell and facts.unknown_write:
                    return _WRITTEN_SCRIPT
                if text is not None and _mentions_process_kill(text):
                    _collect_process_facts(text, facts, 1)
    return None


def _shell_script_text(path: str, by_shell: bool) -> str | None:
    """The text of a script a shell reads, or of an executable shell script; None otherwise."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(1_048_577)
    except OSError:
        return None
    if len(data) > 1_048_576 or b"\0" in data[:4096]:
        return None
    text = data.decode(errors="replace")
    first = text.split("\n", 1)[0]
    if not by_shell and first.startswith("#!"):
        interpreter = first[2:].split()
        names = [os.path.basename(word) for word in interpreter[:2]]
        if not set(names) & _PROCESS_SHELLS:
            return None
    return text


def _mentions_process_kill(text: str) -> bool:
    """Whether text names a kill program or selector as a word once quoting is removed."""
    try:
        text = _decode_ansi_c_quotes(text)
    except ValueError:
        return True
    text = re.sub(r"\\\n|['\"\\]", "", text)
    return bool(re.search(r"(?<![\w.-])(?:kill|pkill|killall|pgrep|pidof)(?![\w.-])", text))


_ASSIGNING_BUILTINS = {
    "read",
    "mapfile",
    "readarray",
    "getopts",
    "declare",
    "typeset",
    "local",
    "export",
    "readonly",
    "let",
}


def _may_set_ifs(command: str) -> bool:
    """Whether text assigns IFS in a form the segment reader does not see.

    Assignments by words and builtins are found per segment, at every depth, by
    `_record_assigning`. What remains is `${IFS:=...}` and arithmetic, whose
    expansions can name any variable. Here-document bodies are data and skipped.
    """
    try:
        text = re.sub(r"\\\n|['\"\\]", "", _decode_ansi_c_quotes(preprocess_shell_command(command)))
    except (ValueError, ShellPreprocessLimit):
        return True
    return bool(re.search(r"\$\{\s*IFS\s*:?[=?]|\(\([^)]*(?:IFS|[$`])", text))


def _may_rebind_echo(command: str) -> bool:
    """Whether the command defines a function, alias or builtin that could be `echo`."""
    try:
        tokens = _process_tokens(command)
    except ValueError:
        return True
    values = [_shell_word_value(token) for token in tokens]
    for index, value in enumerate(values):
        if value in {"alias", "enable"}:
            return True
        # `NAME() ...` and `function NAME`: a name the reader cannot read could be echo.
        if tokens[index + 1 : index + 3] == ["(", ")"] and value in {None, "echo"}:
            return True
        if value == "function" and index + 1 < len(values) and values[index + 1] in {None, "echo"}:
            return True
    return False


def _echo_output(body: str) -> str | None:
    """The output of a substitution that is one plain `echo` of literal words, else None."""
    try:
        pipelines = _process_pipelines(body)
    except ValueError:
        return None
    if len(pipelines) != 1 or len(pipelines[0]) != 1:
        return None
    values = [_shell_word_value(word) for word in pipelines[0][0]]
    # echo reads only leading -n, -e and -E words as options, and with xpg_echo
    # interprets backslashes, so output holding one is not predicted.
    if values[:1] != ["echo"] or None in values or re.fullmatch(r"-[neE]+", values[1] if len(values) > 1 else ""):
        return None
    output = " ".join(value for value in values[1:] if value is not None)
    return None if "\\" in output else output


def _inline_echo_substitutions(executable: str, substitutions: dict[str, tuple[str, str]]) -> str:
    """Replace each plain-echo substitution with its output, quoted for where it stands."""
    for marker, (_, body) in substitutions.items():
        output = _echo_output(body)
        start = executable.find(marker)
        if output is None or start < 0:
            continue
        quoted = shell_quote_after(executable[:start], "") == '"'
        if quoted:
            text = re.sub(r'([\\"$`])', r"\\\1", output)
        elif re.fullmatch(r"[A-Za-z0-9 _./=:,+@%-]*", output):
            # Unquoted output is split into words, as the reader splits plain text.
            text = output
        else:
            continue
        executable = executable[:start] + text + executable[start + len(marker) :]
    return executable


def _collect_process_facts(command: str, facts: _ProcessFacts, depth: int = 0) -> None:
    """Record kill sites, selectors and unreadable parts across one invocation.

    Statements, substitutions and nested shell scripts all count, without data
    flow between them, so a selection reaches its kill however the PIDs travel.
    """
    if depth >= 12:
        facts.limit = True
        return
    try:
        executable, substitutions = _hide_substitutions(preprocess_shell_command(command))
    except ShellPreprocessLimit:
        facts.limit = True
        return
    try:
        # Effects carried at this level count for the whole invocation.
        facts.ifs_set = facts.ifs_set or _may_set_ifs(command)
        facts.echo_rebound = facts.echo_rebound or _may_rebind_echo(command)
        prior_rebound = facts.prior is not None and facts.prior.echo_rebound
        if not (_may_rebind_echo(facts.command) or prior_rebound or facts.echo_rebound):
            # Only while the command cannot rebind `echo` to something else.
            executable = _inline_echo_substitutions(executable, substitutions)
        pipelines = _process_pipelines(_decode_ansi_c_quotes(executable))
    except ValueError:
        facts.limit = True
        return
    if depth == 0:
        _record_assignments(executable, facts)
    _record_effects(pipelines, facts)
    for _, body in substitutions.values():
        _collect_process_facts(body, facts, depth + 1)
    # Bash's own words read a spliced word whole (`'pk'"ill"`). The shared
    # lexer's words are read only for the shell rule's refusals of unreadable options.
    # The shared parser keeps an expanding here-document's substitutions as lines
    # of their own; they fill the document and run no command of their own.
    bodies = [body for documents in facts.documents().values() for body, quoted in documents if not quoted]
    fillers = {marker for marker, (_, body) in substitutions.items() if any(body in text for text in bodies)}
    for pipeline in pipelines:
        for segment in pipeline:
            if segment != [next(iter(fillers & set(segment)), None)]:
                _segment_process_facts(segment, facts, depth)
    for pipeline in _pipelines(executable):
        for segment in pipeline:
            found = _command_at(segment)
            if found is not None and (
                found[0] == "__UNDECIDABLE_SECRET_COMMAND__"
                or (found[0] in _PROCESS_SHELLS and "__UNDECIDABLE_SECRET_COMMAND__" in _shell_script(found[1]))
            ):
                facts.limit = True


class _Process:
    """One protected process as the kill programs see it."""

    def __init__(self, pid: int) -> None:
        try:
            with open(f"/proc/{pid}/stat", "rb") as handle:
                stat = handle.read()
            with open(f"/proc/{pid}/cmdline", "rb") as handle:
                argv = [part.decode(errors="replace") for part in handle.read().split(b"\0")]
            with open(f"/proc/{pid}/status", encoding="utf-8", errors="replace") as handle:
                uid_line = next(line for line in handle if line.startswith("Uid:"))
        except (OSError, StopIteration) as exc:
            raise _Unresolvable from exc
        head, _, tail = stat.rpartition(b")")
        fields = tail.split()
        self.pid = pid
        self.comm = head.split(b"(", 1)[1].decode(errors="replace")
        self.ppid = int(fields[1])
        self.pgid = int(fields[2])
        self.argv0 = argv[0] if argv else ""
        self.ruid = int(uid_line.split()[1])


class _ProcessTable:
    """The processes a kill must not reach, with read-only queries against them.

    They are every live ancestor of this hook, from its launcher through the
    harness to PID 1, and the agent's own shell. That shell does not exist yet,
    so one stand-in per installed POSIX shell name waits on a pipe in its place;
    only properties a stand-in shares with it (name, credentials) are queried.
    """

    def __init__(self, exec_names: set[str] = frozenset(), *, any_user: bool = False) -> None:  # type: ignore[assignment]
        self.exec_names = {name for name in exec_names if name}
        # The command changes credentials, so ID filters cannot tell the shell apart.
        self.any_user = any_user
        self._ancestors: list[_Process] | None = None
        self._stand_ins: list[subprocess.Popen[str]] = []
        self._stand_in_processes: list[_Process] | None = None

    def __enter__(self) -> _ProcessTable:
        return self

    def __exit__(self, *_: object) -> None:
        for stand_in in self._stand_ins:
            if stand_in.stdin is not None:
                stand_in.stdin.close()
        for stand_in in self._stand_ins:
            try:
                stand_in.wait(timeout=1)
            except subprocess.TimeoutExpired:
                stand_in.kill()
                stand_in.wait()

    @property
    def ancestors(self) -> list[_Process]:
        if self._ancestors is None:
            ancestors: list[_Process] = []
            pid = os.getppid()
            while pid > 0 and len(ancestors) < 1024:
                ancestors.append(_Process(pid))
                pid = ancestors[-1].ppid
            if not ancestors:
                raise _Unresolvable
            self._ancestors = ancestors
        return self._ancestors

    def protected(self) -> list[_Process]:
        if self._stand_in_processes is None:
            bash = shutil.which("bash")
            if bash is None:
                raise _Unresolvable
            launches = [
                ([path, "-c", "echo ready; read -r line"], path)
                for path in map(shutil.which, sorted(_PROCESS_SHELLS))
                if path
            ]
            # A program the command execs takes over the shell's PID: a stand-in
            # renames itself to that program's comm and argv0.
            launches += [
                ([name, "-c", 'printf %s "${0##*/}" > /proc/self/comm; echo ready; read -r line'], bash)
                for name in sorted(self.exec_names)
            ]
            for argv, executable in launches:
                try:
                    stand_in = subprocess.Popen(
                        argv,
                        executable=executable,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True,
                    )
                except (OSError, ValueError) as exc:
                    raise _Unresolvable from exc
                self._stand_ins.append(stand_in)
                if stand_in.stdout is None or stand_in.stdout.readline() != "ready\n":
                    raise _Unresolvable
            self._stand_in_processes = [_Process(stand_in.pid) for stand_in in self._stand_ins]
        return [*self._stand_in_processes, *self.ancestors]

    def _alive(self) -> None:
        if any(stand_in.poll() is not None for stand_in in self._stand_ins):
            raise _Unresolvable

    def pgrep_selects(self, selection: tuple[list[str], set[int] | None] | None) -> bool:
        """Whether `pgrep ARGS`, in any common locale, selects a protected process.

        A parent restriction (`-P`) is applied here from the table: an ancestor's
        parent is known, and the agent's shell counts as a child of every ancestor.
        None is an invocation that only reports, or fails, and selects nothing.
        """
        if selection is None:
            return False
        args, parents = selection
        pgrep = shutil.which("pgrep")
        if pgrep is None:
            raise _Unresolvable
        pids = {process.pid for process in self.protected()}
        found: set[int] = set()
        for locale in (None, "C", "C.UTF-8"):
            env = dict(os.environ) if locale is None else {**os.environ, "LC_ALL": locale}
            result = _run_read_only([pgrep, *args], env)
            # pgrep warns, and matches nothing, for a name longer than a 15-character comm.
            stderr = result.stderr.replace(_PGREP_LONG_NAME_WARNING, "")
            if result.returncode not in {0, 1} or stderr or not re.fullmatch(r"(\d+\n)*", result.stdout):
                raise _Unresolvable
            found.update(int(pid) for pid in result.stdout.split())
        self._alive()
        if parents is not None:
            ancestors = {process.pid for process in self.ancestors}
            pids = {
                process.pid
                for process in self.protected()
                if process.ppid in parents or (process.pid not in ancestors and parents & ancestors)
            }
        return bool(found & pids)

    def pidof_selects(self, args: list[str]) -> bool:
        """Whether `pidof ARGS` lists a protected process."""
        pidof = shutil.which("pidof")
        if pidof is None:
            raise _Unresolvable
        pids = {process.pid for process in self.protected()}
        result = _run_read_only([pidof, *args], dict(os.environ))
        if result.returncode not in {0, 1} or result.stderr or not re.fullmatch(r"[\d ]*\n?", result.stdout):
            raise _Unresolvable
        self._alive()
        return bool({int(pid) for pid in result.stdout.split()} & pids)


def _run_read_only(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=2, env=env)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise _Unresolvable from exc


def _procps_signal(word: str) -> bool:
    """procps 4.0.4 signal_name_to_number() on `word` without its dash, as a predicate."""
    name = word[3:] if word[:3].upper() == "SIG" else word
    if name.upper() in _PROCPS_SIGNALS:
        return True
    if name[:6].upper() == "RTMIN+":
        name = name[6:]
    match = re.fullmatch(r"[ \t\n\v\f\r]*([+-]?\d+)", name)
    return match is not None and 0 <= int(match.group(1)) <= 127 - signal.SIGRTMIN


def _pgrep_selection(
    values: list[str], *, pkill: bool, any_user: bool = False
) -> tuple[list[str], set[int] | None] | None:
    """Rebuild a pgrep or pkill selection as canonical pgrep arguments, or refuse it."""
    if pkill:
        # procps signal_option(): the first dashed word that names a signal is removed.
        for index, value in enumerate(values):
            if value.startswith("-") and _procps_signal(value[1:]):
                values = values[:index] + values[index + 1 :]
                break
    try:
        options, operands = getopt.gnu_getopt(values, _PKILL_SHORT if pkill else _PGREP_SHORT, _PGREP_LONG)
    except getopt.GetoptError as exc:
        raise _Unresolvable from exc
    if len(operands) > 1 or (pkill and any(option in {"-v", "-l", "-a", "-d", "-w"} for option, _ in options)):
        raise _Unresolvable
    if any(option in {"-h", "--help", "-V", "--version"} for option, _ in options):
        # Help and version output stop procps before it selects anything.
        return None
    selection: list[str] = []
    parents: set[int] | None = None
    inverse = any(option in {"-v", "--inverse"} for option, _ in options)
    dropped = False
    for option, value in options:
        if option in {"-f", "--full"}:
            raise _Unresolvable(_FULL_MATCH)
        if option in {"-w", "--lightweight"}:
            # Threads carry their own names, which the stand-ins do not have.
            raise _Unresolvable
        if option in _PGREP_SELECTION:
            if _PGREP_SELECTION[option] not in selection:
                selection.append(_PGREP_SELECTION[option])
        elif option in _PGREP_SELECTION_VALUES and not any_user:
            selection += [_PGREP_SELECTION_VALUES[option], value]
        elif option in _PGREP_SELECTION_VALUES:
            # Under sudo or another credential launcher the shell's IDs are not the
            # stand-ins', so an ID filter is dropped, as any narrowing is.
            if inverse:
                raise _Unresolvable
            dropped = True
        elif option in _PGREP_OUTPUT:
            continue
        elif inverse:
            # Under -v, dropping a restriction would narrow the selection.
            raise _Unresolvable
        elif option in {"-P", "--parent"}:
            if not re.fullmatch(r"\d+(?:,\d+)*", value):
                raise _Unresolvable
            parents = (parents or set()) | {int(pid) for pid in value.split(",")}
        else:
            # Sessions, groups, terminals, ages, states, pidfiles, ranking, namespaces
            # and handlers only narrow a selection; the query without them covers it.
            dropped = True
    if not (
        operands or parents is not None or dropped or any(option in _PGREP_SELECTION_VALUES for option, _ in options)
    ):
        # procps refuses a selection without criteria, so nothing is signalled.
        return None
    # A selection by other criteria alone matches every name, filtered as above.
    return [*selection, "--", *(operands or [""])], parents


def _killall_selects(values: list[str], table: _ProcessTable) -> bool:
    """Whether psmisc killall's literal name match can reach a protected process."""
    ignore_case = False
    uid: int | None = None
    names: list[str] = []
    options = True
    index = 0
    while index < len(values):
        value = values[index]
        index += 1
        if not options or value == "-" or not value.startswith("-"):
            names.append(value)
        elif value == "--":
            options = False
        elif value in {"-s", "--signal", "-signal", "-u", "--user", "-user"}:
            if index >= len(values):
                raise _Unresolvable
            if value.lstrip("-") == "user" or value == "-u":
                try:
                    uid = pwd.getpwnam(values[index]).pw_uid
                except KeyError as exc:
                    raise _Unresolvable from exc
            index += 1
        elif value.lstrip("-") in {"exact", "quiet", "verbose", "wait", "ignore-case"} or (
            value[1:] and set(value[1:]) <= set("eqvwI")
        ):
            ignore_case = ignore_case or "I" in value or value.lstrip("-") == "ignore-case"
        elif not _procps_signal(value[1:]):
            # Regexes, process groups, ages, namespaces, contexts and paths are refused.
            raise _Unresolvable
    if not names or any("/" in name for name in names):
        raise _Unresolvable

    def same(left: str, right: str) -> bool:
        return left.lower() == right.lower() if ignore_case else left == right

    for process in table.protected():
        if uid is not None and not table.any_user and process.ruid != uid:
            continue
        program = process.argv0.rsplit("/", 1)[-1]
        # A superset of match_process_name(): the comm, its 15-character prefix,
        # and the long name read from the command line.
        if any(
            same(name, process.comm)
            or same(name[:15], process.comm)
            or same(name, program)
            or same(name, process.argv0)
            for name in names
        ):
            return True
    return False


def _pidof_selection(values: list[str]) -> list[str]:
    """Keep sysvinit pidof's selecting options; output-only and omit options only narrow it."""
    try:
        options, operands = getopt.gnu_getopt(values, "cd:hno:qsxz")
    except getopt.GetoptError as exc:
        raise _Unresolvable from exc
    if not operands or any(option == "-h" for option, _ in options):
        raise _Unresolvable
    return [*(option for option, _ in options if option in {"-c", "-n", "-x", "-z"}), *operands]


def _kill_operands(raw: tuple[str, ...], fed: bool, table: _ProcessTable) -> tuple[str | None, bool]:
    """Check kill's operands; return a refusal and whether any operand is not literal."""
    words = list(raw)
    index = 0
    signal_seen = False
    while index < len(words):
        value = _shell_word_value(words[index])
        if value in {"-l", "-L"}:
            return None, False
        if value in {"-s", "-n"}:
            index += 2
            signal_seen = True
        elif value == "--":
            index += 1
            break
        elif value is not None and value.startswith("-") and len(value) > 1 and not signal_seen:
            # The first signal word; later dashed numbers are process groups.
            index += 1
            signal_seen = True
        else:
            break
    operands = words[index:]
    dynamic = fed or not operands
    for word in operands:
        if _SELF_PID_EXPANSION.search(word):
            return _SELF_MATCH, True
        value = _shell_word_value(word)
        # Bash reads kill operands with its integer parser: surrounding whitespace,
        # a sign and leading zeros are allowed (`+0`, `" -1"`).
        match = re.fullmatch(r"\s*([+-]?\d+)\s*", value or "")
        if match is None:
            dynamic = True
            continue
        number = int(match.group(1))
        if number in {0, -1}:
            return _SELF_MATCH, dynamic
        if number > 0 and number in {process.pid for process in table.ancestors}:
            return _SELF_MATCH, dynamic
        if number < 0 and -number in {process.pgid for process in table.ancestors}:
            return _SELF_MATCH, dynamic
    return None, dynamic


def _process_values(raw: tuple[str, ...]) -> list[str]:
    values = [_shell_word_value(word) for word in raw]
    if any(value is None for value in values):
        raise _Unresolvable
    return [value for value in values if value is not None]


def _resolve_process_calls(calls: list[tuple[str, tuple[str, ...], bool]], table: _ProcessTable) -> str | None:
    nonliteral = False
    for name, raw, fed in calls:
        if name == "kill":
            reason, dynamic = _kill_operands(raw, fed, table)
            if reason:
                return reason
            nonliteral = nonliteral or dynamic
        elif (
            name == "pkill"
            and table.pgrep_selects(_pgrep_selection(_process_values(raw), pkill=True, any_user=table.any_user))
        ) or (name == "killall" and _killall_selects(_process_values(raw), table)):
            return _SELF_MATCH
    # A kill whose PIDs come from elsewhere is paired with every selector in the
    # invocation, however the PIDs travel between them.
    if nonliteral:
        for name, raw, _ in calls:
            if name == "pgrep" and table.pgrep_selects(
                _pgrep_selection(_process_values(raw), pkill=False, any_user=table.any_user)
            ):
                return _SELF_MATCH
            if name == "pidof" and table.pidof_selects(_pidof_selection(_process_values(raw))):
                return _SELF_MATCH
    return None


def _process_refusal(command: str, cwd: str | None = None) -> str | None:
    """Return why a command's process kills are refused, or None to allow them."""
    facts: _ProcessFacts | None = None
    for _ in range(4):
        # Re-read until the effects found anywhere (IFS, echo bindings) are stable.
        reading = _ProcessFacts(command, cwd, facts)
        _collect_process_facts(command, reading)
        settled = facts is not None and reading.effects() == facts.effects()
        facts = reading
        if settled:
            break
    assert facts is not None
    script_reason = _script_reason(facts)
    if facts.limit:
        return "nested shell command could not be parsed safely"
    if facts.opaque:
        return (
            "the command runs shell text the guard cannot read, which could stop the agent's own process; "
            "write that text out as literal commands instead of piping, evaluating or splitting it"
        )
    if facts.unresolved:
        return (
            "a command name the guard cannot resolve could stop the agent's own process; "
            'name the program literally, or quote an expansion ("$PY", not $PY)'
        )
    if script_reason:
        return script_reason
    if not facts.calls:
        return None
    try:
        with _ProcessTable(facts.exec_names, any_user=facts.credential_change) as table:
            return _resolve_process_calls(facts.calls, table)
    except _Unresolvable as exc:
        return exc.args[0] if exc.args else "a process kill could not be resolved against the live process table"


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
    # Rejoined shell words also read a script spliced from quote fragments
    # whole (`bash -c 'en'"v" _`), as the process check reads it.
    for pipeline in _pipelines(executable, shell_words=True):
        for segment in pipeline:
            found = _command_at(segment)
            if found is None or found[0] not in _PROCESS_SHELLS:
                continue
            args = found[1]
            for marker, (prefix, body) in substitutions.items():
                spelling = prefix + body + ("`" if prefix.startswith("`") else ")")
                args = [arg.replace(marker, spelling) for arg in args]
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


def _self_test() -> int:
    """Block the seeded echo shapes. Used by pre-commit; prints no secret values."""
    seeded = (
        "cat ~/.secrets/*",
        "env | grep KEY",
        "printenv *_KEY",
    )
    for command in seeded:
        if _scan_command(command, set()) is None:
            sys.stderr.write("no-print hook did not block a seeded command\n")
            return 1
    return 0


def _main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--self-test"]:
        return _self_test()
    # The secret-output override does not cover process kills.
    override = os.environ.get("LEARN_UK_SECRETS_OK") == "1"

    payload = _read_payload()
    if payload is None or not isinstance(payload.get("tool_input", {}), dict):
        if override:
            return 0
        sys.stderr.write(_block_msg("malformed hook payload"))
        return 2
    if not isinstance(payload.get("tool_input", {}).get("command", ""), str):
        if override:
            return 0
        sys.stderr.write(_block_msg("malformed hook command"))
        return 2
    command = _command(payload)
    if not command:
        return 0

    # Fail closed: the override never covers a process kill or a command the
    # process reader cannot read whole.
    cwd = payload.get("cwd")
    process_reason = _process_refusal(command, cwd if isinstance(cwd, str) and os.path.isabs(cwd) else None)
    if process_reason:
        sys.stderr.write(_process_block_msg(process_reason))
        return 2
    if override:
        return 0

    try:
        reason = _scan_command(command, set())
    except ShellPreprocessLimit:
        reason = "nested shell command could not be parsed safely"
    if reason:
        sys.stderr.write(_block_msg(reason))
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except Exception:
        sys.stderr.write(_block_msg("cannot inspect command"))
        return 2


if __name__ == "__main__":
    sys.exit(main())
