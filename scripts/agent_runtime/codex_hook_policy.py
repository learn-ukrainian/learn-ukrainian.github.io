#!/usr/bin/env python3
"""Run Codex PreToolUse guards with isolated, fail-closed deadlines."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import runpy
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

LOCAL_BASH_GUARDS = (
    ("heal-core-bare.py", 3),
    ("guard-branch-switch-in-main.py", 3),
    ("guard-secret-print.py", 5),
)
ENFORCE_VENV_TIMEOUT = 3
PRIMARY_WRITE_GUARD = ("guard-primary-checkout-write.py", 5)
# These guards answer by rewriting the command (``updatedInput``), which Codex
# ignores. Running them here turns any rewrite into a block instead of letting
# the call proceed unshimmed.
REWRITE_BASH_GUARDS = (("guard-public-github-text.py", 5),)
MERGE_GUARDS = (
    ("guard-admin-merge.py", 20),
    ("guard-pr-merge.py", 20),
)


@dataclass(frozen=True)
class GuardResult:
    name: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_guard(
    python_bin: Path,
    guard: Path,
    payload: str,
    timeout_seconds: float,
) -> GuardResult:
    """Run one guard and convert a deadline expiry into a blocking result."""
    try:
        completed = subprocess.run(
            [str(python_bin), str(guard)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except OSError:
        return GuardResult(guard.name, 2, "", "Codex hook guard unavailable; blocking fail-closed.\n")
    except subprocess.TimeoutExpired as exc:
        return GuardResult(
            name=guard.name,
            returncode=2,
            stdout=_timeout_text(exc.stdout),
            stderr=(
                _timeout_text(exc.stderr) + f"Codex hook guard {guard.name} exceeded {timeout_seconds:g}s; "
                "blocking the tool call fail-closed.\n"
            ),
            timed_out=True,
        )

    return GuardResult(
        name=guard.name,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _emit(result: GuardResult) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def _tool_name(payload: str) -> str:
    try:
        decoded = json.loads(payload or "{}")
    except (json.JSONDecodeError, TypeError):
        return ""
    value = decoded.get("tool_name") if isinstance(decoded, dict) else None
    return value if isinstance(value, str) else ""


def _run_specs(
    python_bin: Path,
    hooks_dir: Path,
    payload: str,
    specs: tuple[tuple[str, int], ...],
) -> list[GuardResult]:
    return [run_guard(python_bin, hooks_dir / name, payload, timeout) for name, timeout in specs]


def _run_merge_guards(
    python_bin: Path,
    hooks_dir: Path,
    payload: str,
) -> list[GuardResult]:
    """Run independent network guards concurrently, return configured order."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MERGE_GUARDS)) as pool:
        futures = [
            pool.submit(run_guard, python_bin, hooks_dir / name, payload, timeout) for name, timeout in MERGE_GUARDS
        ]
        return [future.result() for future in futures]


def _run_enforce_venv(
    hooks_dir: Path,
    canonical_root: Path,
    payload: str,
) -> GuardResult:
    environment = os.environ.copy()
    environment["LEARN_UK_CANONICAL_ROOT"] = str(canonical_root)
    guard = hooks_dir / "enforce-venv.sh"
    try:
        completed = subprocess.run(
            ["/bin/bash", str(guard)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            timeout=ENFORCE_VENV_TIMEOUT,
            env=environment,
        )
    except OSError:
        return GuardResult(guard.name, 2, "", "Codex hook guard unavailable; blocking fail-closed.\n")
    except subprocess.TimeoutExpired as exc:
        return GuardResult(
            name=guard.name,
            returncode=2,
            stdout=_timeout_text(exc.stdout),
            stderr=(
                _timeout_text(exc.stderr) + f"Codex hook guard {guard.name} exceeded "
                f"{ENFORCE_VENV_TIMEOUT}s; blocking the tool call fail-closed.\n"
            ),
            timed_out=True,
        )
    return GuardResult(
        name=guard.name,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _result_code(results: list[GuardResult]) -> int:
    normalized: list[GuardResult] = []
    for result in results:
        if result.stdout:
            result = GuardResult(
                name=result.name,
                returncode=2,
                stdout="",
                stderr=(
                    result.stderr + f"Codex hook guard {result.name} wrote unexpected stdout; "
                    "blocking fail-closed to preserve the single JSON response channel.\n" + result.stdout
                ),
                timed_out=result.timed_out,
            )
        normalized.append(result)
        _emit(result)
    return 2 if any(result.returncode for result in normalized) else 0


def _expand_braces(text: str, max_depth: int = 5, max_variants: int = 64) -> list[str] | None:
    pattern = re.compile(r"\{([^{}\s]+)\}")
    current = [text]
    for _ in range(max_depth):
        next_level = []
        any_expanded = False
        for s in current:
            m = pattern.search(s)
            if not m:
                next_level.append(s)
                continue
            any_expanded = True
            content = m.group(1)
            prefix = s[: m.start()]
            suffix = s[m.end() :]
            range_m = re.match(r"^([a-zA-Z0-9]+)\.\.([a-zA-Z0-9]+)(?:\.\.([+-]?[0-9]+))?$", content)
            if range_m:
                c1, c2, step_str = range_m.groups()
                step = int(step_str) if step_str is not None else 1
                if step == 0:
                    step = 1
                if c1.isdigit() and c2.isdigit():
                    n1, n2 = int(c1), int(c2)
                    if n1 <= n2:
                        items = [str(i) for i in range(n1, n2 + 1, abs(step))]
                    else:
                        items = [str(i) for i in range(n1, n2 - 1, -abs(step))]
                elif len(c1) == 1 and len(c2) == 1:
                    o1, o2 = ord(c1), ord(c2)
                    if o1 <= o2:
                        items = [chr(c) for c in range(o1, o2 + 1, abs(step))]
                    else:
                        items = [chr(c) for c in range(o1, o2 - 1, -abs(step))]
                else:
                    items = content.split(",")
            else:
                items = content.split(",")
            for it in items:
                next_level.append(prefix + it + suffix)
                if len(next_level) > max_variants:
                    return None
        current = next_level
        if not any_expanded:
            break
    if any("{" in s and "}" in s for s in current):
        return None
    return current


def _has_unescaped_metachars(command: str) -> bool:
    single = False
    double = False
    escaped = False
    for index, char in enumerate(command):
        if escaped:
            escaped = False
            continue
        if char == "\\" and not single:
            escaped = True
            continue
        if char == "'" and not double:
            single = not single
            continue
        if char == '"' and not single:
            double = not double
            continue
        if not single:
            if char in ";|&\n<>{}`()":
                return True
            if char == "$" and index + 1 < len(command) and not command[index + 1].isspace():
                return True
        if double:
            if char in ";`()":
                return True
            if char == "$" and index + 1 < len(command) and not command[index + 1].isspace():
                return True
    return False


def _is_safe_data_mention(command: str) -> bool:
    if _has_unescaped_metachars(command):
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    if not words:
        return False
    if _is_ambiguous_or_gh_word(words[0]):
        return False
    cmd = Path(words[0]).name
    if cmd in {"echo", "printf"}:
        return True
    return bool(
        cmd == "git"
        and len(words) > 1
        and words[1]
        in {
            "commit",
            "log",
            "diff",
            "status",
            "show",
            "branch",
            "checkout",
            "add",
        }
    )


def _is_ambiguous_or_gh_word(word: str) -> bool:
    if Path(word).name == "gh":
        return True
    if any(c in word for c in "$`{}<>*?["):
        return True
    return bool("\\x" in word or "\\0" in word)


_WRAPPERS = {
    "sudo",
    "nice",
    "nohup",
    "flock",
    "time",
    "timeout",
    "xargs",
    "env",
    "command",
    "exec",
    "eval",
    "bash",
    "sh",
    "zsh",
    "dash",
    "ash",
    "busybox",
}


def _scan_tokens(tokens: list[str], recognize_gh: object) -> bool:
    expecting_command = True
    wrapper = False
    wrapper_name = None
    shell_dash_c = False

    i = 0
    while i < len(tokens):
        word = tokens[i]
        i += 1

        if word in {"$(", "<(", ">("} or word == "`":
            expecting_command = True
            wrapper = False
            wrapper_name = None
            continue

        if word in {";", "|", "&", "&&", "||", "|&", "\n", "(", "do", "then", "else", "elif", "{"}:
            expecting_command = True
            wrapper = False
            wrapper_name = None
            shell_dash_c = False
            continue

        if word in {")", "}"}:
            expecting_command = False
            wrapper = False
            wrapper_name = None
            continue

        if word.isdigit() and i < len(tokens) and (
            tokens[i] in {"<", ">", ">>", "<&", ">&", "&>", "<>", ">|", "&>>"}
            or tokens[i].startswith(("<", ">"))
        ):
            word = tokens[i]
            i += 1

        if (
            word in {"<", ">", ">>", "<&", ">&", "&>", "<>", ">|", "&>>"}
            or ((word.startswith("<") or word.startswith(">")) and word not in {"<(", ">("})
        ):
            if word not in {"2>&1", "1>&2", "<&0", "<&1", "<&2", ">&1", ">&2"} and i < len(tokens):
                i += 1
            continue

        if expecting_command:
            if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*=", word):
                continue

            if _is_ambiguous_or_gh_word(word):
                return True

            base = Path(word).name
            if base in _WRAPPERS:
                wrapper = True
                wrapper_name = base
                if base == "eval":
                    remaining = " ".join(tokens[i:])
                    return _invokes_or_ambiguous_gh(remaining, recognize_gh)
                elif base in {"bash", "sh", "zsh", "dash", "ash"}:
                    expecting_command = False
                    shell_dash_c = True
                    continue
                else:
                    expecting_command = False
                    continue
            else:
                expecting_command = False
                wrapper = False
                continue

        if shell_dash_c:
            if word in {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}:
                if i < len(tokens):
                    i += 1
                continue

            if (word.startswith("-") and not word.startswith("--") and "c" in word[1:]) or word == "-c" or word == "<<<":
                if i < len(tokens):
                    subcmd = tokens[i]
                    i += 1
                    if _invokes_or_ambiguous_gh(subcmd, recognize_gh):
                        return True
                shell_dash_c = False
                continue

            if (word.startswith("-") or word.startswith("+")) and word != "--":
                continue

            if word == "--":
                shell_dash_c = False
                continue

            if _is_ambiguous_or_gh_word(word):
                return True
            shell_dash_c = False

        if wrapper:
            if wrapper_name == "flock":
                if word in {"-w", "--wait", "--timeout", "-E", "--conflict-exit-code"}:
                    if i < len(tokens):
                        i += 1
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if i < len(tokens) and tokens[i] in {"-c", "--command"}:
                    i += 1
                    if i < len(tokens):
                        subcmd = tokens[i]
                        i += 1
                        if _invokes_or_ambiguous_gh(subcmd, recognize_gh):
                            return True
                    wrapper = False
                    wrapper_name = None
                    continue
                else:
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue

            elif wrapper_name == "timeout":
                if word in {"-s", "--signal", "-k", "--kill-after"}:
                    if i < len(tokens):
                        i += 1
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if re.match(r"^\d+(?:\.\d+)?[smhdSMHD]?$", word):
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue

            elif wrapper_name == "sudo":
                if word in {
                    "-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt",
                    "-r", "--role", "-t", "--type", "-C", "--close-from", "-D", "--chdir",
                    "-T", "--command-timeout",
                }:
                    if i < len(tokens):
                        i += 1
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if word == "--":
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

            elif wrapper_name == "nice":
                if word in {"-n", "--adjustment"}:
                    if i < len(tokens):
                        i += 1
                    continue
                if (word.startswith("-") or word.startswith("+")) and word != "--":
                    continue
                if word == "--":
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

            elif wrapper_name == "env":
                if word in {"-u", "--unset", "-C", "--chdir"}:
                    if i < len(tokens):
                        i += 1
                    continue
                if word in {"-S", "--split-string"}:
                    if i < len(tokens):
                        subcmd = tokens[i]
                        i += 1
                        if _invokes_or_ambiguous_gh(subcmd, recognize_gh):
                            return True
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if word == "--":
                    continue
                if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*=", word):
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

            elif wrapper_name == "exec":
                if word == "-a":
                    if i < len(tokens):
                        i += 1
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if word == "--":
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

            elif wrapper_name == "xargs":
                if word in {
                    "-a", "--arg-file", "-d", "--delimiter", "-E", "-e", "--eof",
                    "-I", "-i", "--replace", "-L", "-l", "--max-lines", "-n", "--max-args",
                    "-P", "--max-procs", "-s", "--max-chars",
                }:
                    if i < len(tokens):
                        i += 1
                    continue
                if word.startswith("-") and word != "--":
                    continue
                if word == "--":
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

            elif wrapper_name in {"nohup", "time", "command", "busybox"}:
                if word.startswith("-") and word != "--":
                    continue
                if word == "--":
                    expecting_command = True
                    wrapper = False
                    wrapper_name = None
                    continue
                i -= 1
                expecting_command = True
                wrapper = False
                wrapper_name = None
                continue

        if word in {"-exec", "-execdir", "-ok", "-okdir"}:
            expecting_command = True
            wrapper = False
            wrapper_name = None
            continue

    return False


def _invokes_or_ambiguous_gh(command: str, recognize_gh: object) -> bool:
    """Recognize command positions, shell expansions, and wrappers hiding gh.

    Fail closed: returns False only if every command is a proven literal non-gh command
    or safe data mention.
    """
    if _is_safe_data_mention(command):
        return False

    if re.search(r"\bgh\b", command):
        return True
    if re.search(r"\b(issue|pr)\s+(create|edit|close|comment|merge|ready)\b", command):
        return True

    variants = _expand_braces(command)
    if variants is None:
        return True

    for variant in variants:
        if callable(recognize_gh) and recognize_gh(variant):
            return True
        try:
            lexer = shlex.shlex(variant, posix=True, punctuation_chars=";|&()\n`<>")
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            return True

        if _scan_tokens(tokens, recognize_gh):
            return True

    return False


def _publication_command_code(payload: str, hooks_dir: Path) -> int:
    """Admit only a literal, single gh call resolving to the tracked shim.

    Codex cannot apply updatedInput. Shell composition and expansions cannot
    establish that every publication uses the shim, so refuse those calls.
    Other commands still go through the existing shared guards.
    """
    decoded = json.loads(payload)
    command = decoded.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        return 2

    try:
        recognize = runpy.run_path(str(hooks_dir / "guard-public-github-text.py"))["invokes_gh"]
    except (OSError, SyntaxError, KeyError):
        print("Codex publication guard is unavailable; blocking fail-closed.", file=sys.stderr)
        return 2

    if not _invokes_or_ambiguous_gh(command, recognize):
        return 0

    safe = not any(char in command for char in ";&|()$`\n<>\\{}")
    try:
        words = shlex.split(command)
    except ValueError:
        print("Codex publication command cannot be parsed; blocking fail-closed.", file=sys.stderr)
        return 2

    while words and words[0] in {"env", "/usr/bin/env", "command", "exec"}:
        words.pop(0)
        if words and words[0] == "--":
            words.pop(0)

    safe = safe and bool(words) and words[0] == "gh"
    shim = hooks_dir.parents[2] / "scripts/agent_runtime/shims/gh"
    resolved = shutil.which("gh")
    safe = safe and resolved is not None and Path(resolved).resolve() == shim.resolve()
    if not safe:
        print("Codex publication command is not fully shim guarded; blocking fail-closed.", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", type=Path, required=True)
    parser.add_argument("--hooks-dir", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    args = parser.parse_args()
    payload = sys.stdin.read()
    tool_name = _tool_name(payload)
    try:
        decoded = json.loads(payload or "{}")
        if not isinstance(decoded, dict):
            raise ValueError("invalid payload")
    except ValueError:
        print("Codex tool payload is invalid; blocking fail-closed.", file=sys.stderr)
        return 2
    tool_input = decoded.get("tool_input", {})
    if tool_name == "write_stdin" or (tool_name == "Bash" and isinstance(tool_input, dict) and "chars" in tool_input):
        print("Codex interactive input cannot be command guarded; blocking fail-closed.", file=sys.stderr)
        return 2
    if tool_name == "Bash":
        venv_result = _run_enforce_venv(
            args.hooks_dir,
            args.canonical_root,
            payload,
        )
        if _result_code([venv_result]):
            return 2
        publication_code = _publication_command_code(payload, args.hooks_dir)
        if publication_code:
            return publication_code

    local_specs = (*LOCAL_BASH_GUARDS, *REWRITE_BASH_GUARDS) if tool_name == "Bash" else ()
    local_results = _run_specs(
        args.python_bin,
        args.hooks_dir,
        payload,
        (*local_specs, PRIMARY_WRITE_GUARD),
    )
    local_code = _result_code(local_results)
    if local_code:
        return local_code

    if tool_name == "Bash":
        merge_code = _result_code(_run_merge_guards(args.python_bin, args.hooks_dir, payload))
        if merge_code:
            return merge_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
