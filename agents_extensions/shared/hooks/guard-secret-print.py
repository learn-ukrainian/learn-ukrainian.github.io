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

Quote-aware tokenization keeps dangerous-looking strings inside a quoted commit
message from becoming false positives. If parsing is uncertain, the hook allows
the command; this is a guardrail, not a shell interpreter.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

SEPARATORS = {"&&", "||", ";"}
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

_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*\Z")
_VAR_REF_RE = re.compile(
    r"(?<!\\)\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)(?::[-=?+][^}]*)?\}|"
    r"(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _tokenize(command: str) -> list[str]:
    try:
        return shlex.split(_strip_heredoc_bodies(command), posix=False)
    except ValueError:
        return []


def _strip_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _is_single_quoted(token: str) -> bool:
    return len(token) >= 2 and token[0] == token[-1] == "'"


def _is_assignment(token: str) -> bool:
    return bool(_ASSIGNMENT_RE.match(_strip_quotes(token)))


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
        if j < len(tokens) and tokens[j] == "-":
            strip_tabs = True
            j += 1
        if j < len(tokens):
            delimiter = _strip_quotes(tokens[j])
            if delimiter:
                delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    if "<<" not in command:
        return command

    kept: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.splitlines():
        if pending:
            delimiter, strip_tabs = pending[0]
            candidate = line.lstrip("\t") if strip_tabs else line
            if candidate == delimiter:
                pending.pop(0)
            continue
        kept.append(line)
        pending.extend(_heredoc_delimiters(line))
    return "\n".join(kept)


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
        elif token in SEPARATORS:
            flush_pipeline()
        else:
            segment.append(token)
    flush_pipeline()
    return pipelines


def _command_at(seg: list[str]) -> tuple[str, list[str], int] | None:
    """Return `(command, raw_args, index)` after simple wrappers/assignments."""
    i = 0
    while i < len(seg) and _is_assignment(seg[i]):
        i += 1
    while i < len(seg) and _strip_quotes(seg[i]) in {"sudo", "time", "nohup", "command"}:
        i += 1
        while i < len(seg) and _is_assignment(seg[i]):
            i += 1
    if i >= len(seg):
        return None

    cmd = _strip_quotes(seg[i])
    if cmd != "env":
        return cmd, seg[i + 1 :], i

    # `env` is both a dump command and a wrapper. If a real command follows
    # options/assignments, return that command; otherwise return env itself.
    j = i + 1
    while j < len(seg):
        token = _strip_quotes(seg[j])
        if _is_assignment(seg[j]):
            j += 1
            continue
        if token in {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"} and j + 1 < len(seg):
            j += 2
            continue
        if token.startswith("--unset=") or token.startswith("--chdir=") or token.startswith("--split-string="):
            j += 1
            continue
        if token in {"-i", "-0", "--ignore-environment", "--null"}:
            j += 1
            continue
        if token.startswith("-"):
            j += 1
            continue
        break
    if j < len(seg):
        return _strip_quotes(seg[j]), seg[j + 1 :], j
    return "env", seg[i + 1 :], i


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


def _expanded_secret_var(arg: str) -> str | None:
    if _is_single_quoted(arg):
        return None
    for match in _VAR_REF_RE.finditer(arg):
        name = match.group("braced") or match.group("plain") or ""
        if _is_secret_var_name(name):
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


def _display_file_reason(pipeline: list[list[str]], seg_index: int) -> str | None:
    command = _command_at(pipeline[seg_index])
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in DISPLAY_FILE_COMMANDS:
        return None
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


def _echo_secret_reason(seg: list[str]) -> str | None:
    command = _command_at(seg)
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in {"echo", "printf"}:
        return None
    for arg in args:
        secret_name = _expanded_secret_var(arg)
        if secret_name:
            return f"`{cmd}` would print ${secret_name}"
    return None


def _danger_reason(pipeline: list[list[str]]) -> str | None:
    if not pipeline or _has_override(pipeline[0]):
        return None

    reason = _env_dump_reason(pipeline)
    if reason:
        return reason

    for i, segment in enumerate(pipeline):
        reason = _display_file_reason(pipeline, i)
        if reason:
            return reason
        reason = _grep_reason(pipeline, i)
        if reason:
            return reason
        reason = _echo_secret_reason(segment)
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

    for pipeline in _pipelines(command):
        reason = _danger_reason(pipeline)
        if reason:
            sys.stderr.write(_block_msg(reason))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
