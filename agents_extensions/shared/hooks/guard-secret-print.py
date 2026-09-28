#!/usr/bin/env python3
"""PreToolUse guard - block clear secret-value dumps (#M-5 / #1908).

Reads the Claude Code hook payload on stdin (JSON with `tool_input.command`) and
exits 2 (block) when a Bash command would print known secret values into the
transcript. Exit 0 (allow) otherwise.

This guard is deliberately narrow. It catches high-confidence dump shapes only:

  - unfiltered `env` / `printenv` / `set`
  - display commands (`cat`, `bat`, `less`, `head`, `tail`) reading known
    secret files
  - `grep` / `rg` / `ugrep` reading dotenv-style secret files without a
    key-only/count transform
  - `echo` / `printf` expanding known secret environment variables
  - `scripts.session_supervisor worker-env` environment views, including the
    explicit `--all` form

Quote-aware tokenization keeps dangerous-looking strings inside a quoted commit
message from becoming false positives. External file lists (for example,
``xargs cat < list``) and copies whose destination is read later (for example,
``cp .env x; cat x``), as well as values loaded by ``source .env`` or
``. .env`` and printed later, are not modeled. This is defense-in-depth,
not a sandbox.
"""

from __future__ import annotations

import codecs
import json
import os
import re
import shlex
import sys

# Use the sibling helper in either the source tree or a deployed hook copy.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from shell_shlex import (
        skippable_heredoc_delimiters,
        split_quote_preserving,
        strip_skippable_heredoc_bodies,
    )
except ImportError as exc:
    print(f"guard dependency unavailable: shell_shlex ({exc})", file=sys.stderr)
    raise SystemExit(2) from exc

SEPARATORS = {"&&", "||", ";", "&", "\n"}
DISPLAY_FILE_COMMANDS = {"cat", "bat", "less", "head", "tail"}
ENV_DUMP_COMMANDS = {"env", "printenv", "set"}
GREP_COMMANDS = {"grep", "rg", "ugrep"}
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


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


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


def _tokenize(command: str) -> list[str]:
    try:
        executable = _strip_shell_comments(
            _decode_ansi_c_quotes(_strip_heredoc_bodies(_collapse_shell_line_continuations(command)))
        )
        protected, parameters = _protect_parameters(executable)
        tokens = split_quote_preserving(protected, punctuation_chars="();&|<>\n", whitespace=" \t")
        return [_restore_parameters(token, parameters) for token in tokens]
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
    """Return command pipelines, split quote-aware on `|`, `&&`, `||`, and `;`."""
    tokens = _tokenize(command)
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
        if token == "|":
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
        wrapper = _strip_quotes(seg[i])
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

    cmd = _strip_quotes(seg[i])
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


def _is_safe_transform(seg: list[str]) -> bool:
    command = _command_at(seg)
    if command is None:
        return False
    cmd, args, _idx = command
    if cmd == "cut":
        return _cut_is_key_only(args)
    if cmd == "jq":
        return any("keys" in _strip_quotes(arg) for arg in args)
    if cmd == "wc":
        return True
    if cmd in GREP_COMMANDS:
        return _has_short_flag(args, "o") or any(_strip_quotes(arg) == "--only-matching" for arg in args)
    if cmd == "sed":
        return any("=.*//" in _strip_quotes(arg) or "=.*$//" in _strip_quotes(arg) for arg in args)
    if cmd == "awk":
        joined = " ".join(_strip_quotes(arg) for arg in args)
        return "-F=" in joined and "$1" in joined and "$2" not in joined
    return False


def _has_safe_downstream(pipeline: list[list[str]], seg_index: int) -> bool:
    return any(_is_safe_transform(seg) for seg in pipeline[seg_index + 1 :])


def _is_obvious_passthrough(seg: list[str]) -> bool:
    command = _command_at(seg)
    if command is None:
        return False
    cmd, _args, _idx = command
    return cmd in {"bat", "cat", "head", "less", "more", "sort", "tail", "tee"}


def _has_obvious_passthrough_downstream(pipeline: list[list[str]], seg_index: int) -> bool:
    return any(_is_obvious_passthrough(seg) for seg in pipeline[seg_index + 1 :])


def _env_dump_reason(pipeline: list[list[str]]) -> str | None:
    command = _command_at(pipeline[0])
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in ENV_DUMP_COMMANDS:
        return None
    if cmd in {"printenv", "set"} and args:
        return None
    if cmd == "env" and any(not _is_assignment(arg) for arg in args):
        # `env FOO=bar` with no command is still a dump; env options are
        # uncommon in this workflow, so uncertain forms are allowed.
        return None
    if _has_safe_downstream(pipeline, 0):
        return None
    if len(pipeline) > 1 and not _has_obvious_passthrough_downstream(pipeline, 0):
        return None
    return f"`{cmd}` would print the full shell environment"


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


def _display_file_reason(pipeline: list[list[str]], seg_index: int, copied: set[str]) -> str | None:
    command = _command_at(pipeline[seg_index])
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in DISPLAY_FILE_COMMANDS:
        return None
    for index, arg in enumerate(args[:-1]):
        operator = _strip_quotes(arg)
        source = args[index + 1]
        if operator == "<" and _is_known_secret_file(source) and not _has_safe_downstream(pipeline, seg_index):
            return f"`{cmd}` would print known secret file `{_strip_quotes(source)}`"
        if operator == "<<<":
            name = _expanded_secret_var(source, copied)
            if name and not _has_safe_downstream(pipeline, seg_index):
                return f"`{cmd}` would print ${name} from a here-string"
    for arg in _file_args(cmd, args):
        if _is_known_secret_file(arg):
            if _has_safe_downstream(pipeline, seg_index):
                return None
            return f"`{cmd}` would print known secret file `{_strip_quotes(arg)}`"
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
    if _has_short_flag(args, "o") or any(_strip_quotes(arg) == "--only-matching" for arg in args):
        return True
    if _has_short_flag(args, "v") or any(_strip_quotes(arg) == "--invert-match" for arg in args):
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


def _grep_reason(pipeline: list[list[str]], seg_index: int) -> str | None:
    command = _command_at(pipeline[seg_index])
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in GREP_COMMANDS:
        return None
    if _grep_has_safe_flag(cmd, args) or _has_safe_downstream(pipeline, seg_index):
        return None
    for arg in _grep_file_args(args):
        if _is_dotenv_secret_file(arg):
            return f"`{cmd}` would print values from secret file `{_strip_quotes(arg)}`"
    return None


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


def _danger_reason(pipeline: list[list[str]], copied: set[str], named: dict[str, str]) -> str | None:
    if not pipeline or _has_override(pipeline[0]):
        return None

    reason = _env_dump_reason(pipeline)
    if reason:
        return reason

    for i, segment in enumerate(pipeline):
        for index, token in enumerate(segment[:-1]):
            source = segment[index + 1]
            if token == "<" and _is_known_secret_file(source):
                return f"input redirection would read known secret file `{_strip_quotes(source)}`"
            if token == "<<<" and _expanded_secret_var(source, copied, named):
                found = _command_at(segment)
                if found and found[0] != "read":
                    return "here-string would expose a secret value"
        reason = _worker_env_reason(segment)
        if reason:
            return reason
        reason = _display_file_reason(pipeline, i, copied)
        if reason:
            return reason
        reason = _grep_reason(pipeline, i)
        if reason:
            return reason
        reason = _echo_secret_reason(segment, copied, named)
        if reason:
            return reason
        _track_secret_copies(segment, copied, named)
    return None


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


def _shell_script(args: list[str]) -> list[str]:
    """Extract the script operand of a shell -c invocation."""

    def decode(index: int) -> list[str]:
        if index >= len(args):
            return []
        # shlex in preservation mode separates adjacent quoted fragments.
        # Bash concatenates them into one -c word before the child shell runs.
        try:
            words = shlex.split("".join(args[index:]), posix=True)
        except ValueError:
            return [_strip_quotes(args[index])]
        candidates = [words[0]] if words else []
        first = _strip_quotes(args[index])
        if first not in candidates:
            candidates.append(first)
        return candidates

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
                return decode(script_index)
            i = script_index
            continue
        break
    return []


def _scan_command(command: str, copied: set[str], named: dict[str, str] | None = None, *, depth: int = 0) -> str | None:
    if depth >= 12:
        return "shell recursion limit reached while scanning for secret output"
    if named is None:
        named = {}
    executable = _strip_shell_comments(
        _decode_ansi_c_quotes(_strip_heredoc_bodies(_collapse_shell_line_continuations(command)))
    )
    # Scan the complete text first: shlex may expose a separator inside a
    # substitution as a top-level token, but Bash executes its whole body.
    for body in _substitution_bodies(executable):
        reason = _scan_command(body, set(copied), dict(named), depth=depth + 1)
        if reason:
            return reason
    # _pipelines tokenizes and strips here-doc bodies itself. Passing the
    # already decoded text would strip a second time and could turn an exotic
    # delimiter into an identifier before its body is scanned.
    for pipeline in _pipelines(command):
        for segment in pipeline:
            for body in _substitution_bodies(" ".join(segment)):
                reason = _scan_command(body, set(copied), dict(named), depth=depth + 1)
                if reason:
                    return reason
        reason = _danger_reason(pipeline, copied, named)
        if reason:
            return reason
        for segment in pipeline:
            found = _command_at(segment)
            if found is None:
                continue
            cmd, args, _ = found
            if cmd == "__UNDECIDABLE_SECRET_COMMAND__":
                return "shell command could not be parsed safely"
            if cmd == "eval" and args:
                if any(_substitution_bodies(arg) for arg in args) and _eval_secret_source(args, copied, named):
                    return "dynamic eval can reach a known secret source"
                reason = _scan_command(
                    " ".join(_strip_quotes(arg) for arg in args), set(copied), dict(named), depth=depth + 1
                )
                if reason:
                    return reason
            elif cmd in {"bash", "sh", "dash", "zsh", "ksh"}:
                for script in _shell_script(args):
                    reason = _scan_command(script, set(copied), dict(named), depth=depth + 1)
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
    command = _command(payload)
    if not command:
        return 0

    reason = _scan_command(command, set())
    if reason:
        sys.stderr.write(_block_msg(reason))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
