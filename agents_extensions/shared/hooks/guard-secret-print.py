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
# Runtime-computed keys such as os.environ[k], import aliases such as import os
# as o, getattr(os, "environ"), aliases, command-shadowing functions, external
# scripts, computed paths, interpreter aliases and dynamic key assembly remain
# unresolved by this matcher. grep -c TOKEN .env and cp .env backup remain
# conservative denials even though those operations do not print values.

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
ENV_DUMP_COMMANDS = {"env", "printenv", "set", "declare", "export", "typeset"}
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
            flag = re.match(r"(--(?:eval|command)=?|-(?:pe|ne|c|e|E))(?=[\"'])", command[index:])
            if flag:
                out.append(flag[0].rstrip("=") + " ")
                index += flag.end()
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
    if cmd == "printenv":
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


def _program_reason(cmd: str, program: str) -> str | None:
    literal_name = r"(?:[\"'][A-Za-z_][A-Za-z0-9_]*[\"']|:[A-Za-z_][A-Za-z0-9_]*)"
    named_access = rf"\s*(?:\[\s*{literal_name}\s*\]|\.\s*(?:get|fetch)\s*\(\s*{literal_name}\s*[,\)])"
    if _is_python_command(cmd):
        mapping = r"\bos\s*(?:\.\s*environ\b|\[\s*[\"']environ[\"']\s*\])"
    elif cmd == "node":
        mapping = r"\bprocess\s*(?:\.\s*env\b|\[\s*[\"']env[\"']\s*\])"
        named_access += r"|\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*(?![A-Za-z0-9_$]|\s*\()"
    elif cmd == "perl":
        mapping = r"%ENV\b"
        accesses_env = bool(re.search(r"\$ENV\s*\{", program))
    elif cmd == "ruby":
        mapping = r"\bENV\b"
    else:
        return None
    matches = list(re.finditer(mapping, program))
    accesses_env = bool(matches) or (cmd == "perl" and accesses_env)
    whole_env = any(cmd == "perl" or not re.match(named_access, program[match.end() :]) for match in matches)
    for match in re.finditer(r"\b(?:os\s*\.\s*)?getenv\s*\(", program):
        accesses_env = True
        if not re.match(rf"\s*{literal_name}\s*[,\)]", program[match.end() :]):
            whole_env = True
    if whole_env:
        return "inline program can expose the whole environment mapping"
    if accesses_env and any(_is_secret_var_name(name) for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", program)):
        return "inline program can expose a secret environment value"
    if re.search(r"/proc/(?:self|\$\$|[0-9]+)/environ\b", program):
        return "inline program can read environment values"
    return None


def _inline_program_reason(segment: list[str], dumped_files: set[str]) -> str | None:
    found = _command_at(segment)
    if not found:
        return None
    cmd, args, _ = found
    for index, token in enumerate(args):
        token = _strip_quotes(token)
        flag = re.match(r"^(--(?:eval|command)(?:=|$)|-(?:pe|ne|c|e|E))", token)
        if flag:
            attached = token[flag.end() :]
            script_args = [attached, *args[index + 1 :]] if attached else args[index + 1 :]
            for program in _script_words(script_args, 0):
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
